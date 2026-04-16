"""
Hybrid Job Scraper - API-based with Brave browser fallback
Tries fast APIs first, then uses Brave browser automation as fallback
"""

from datetime import datetime
import re
import requests
import time
import os
import random
from concurrent.futures import ThreadPoolExecutor, as_completed, TimeoutError
from urllib.parse import quote_plus
from urllib.parse import unquote

# Scraper Statistics
class ScraperStats:
    """Track scraping statistics"""
    def __init__(self):
        self.start_time = None
        self.jobs_found = {}
        self.errors = []
        self.duration = 0
    
    def start(self):
        self.start_time = time.time()
    
    def record_source(self, source_name, count):
        self.jobs_found[source_name] = count
    
    def record_error(self, source_name, error):
        self.errors.append({"source": source_name, "error": str(error)[:100]})
    
    def end(self):
        if self.start_time:
            self.duration = time.time() - self.start_time
    
    def get_summary(self):
        total = sum(self.jobs_found.values())
        return {
            "total_jobs": total,
            "duration_seconds": round(self.duration, 2),
            "sources_succeeded": len([s for s in self.jobs_found if self.jobs_found[s] > 0]),
            "sources_failed": len(self.errors),
            "jobs_by_source": self.jobs_found,
            "errors": self.errors
        }

_stats = ScraperStats()
TARGET_CITIES = ['Ottawa', 'Kitchener', 'Waterloo', 'Guelph', 'Mississauga', 'Toronto']
ONTARIO_SEARCH_LOCATION = 'Ontario'
ENTRY_LEVEL_SEARCH_TERMS = [
    'ux intern',
    'research intern',
    'ux designer intern',
    'user researcher intern',
    'junior analyst',
    'entry level analyst',
    'entry level designer',
    'entry level researcher'
]
JOBBANK_SEARCH_TERMS = [
    'summer student',
    'student',
    'intern',
    'internship',
    'entry level',
    'junior',
    'graduate',
    'new grad',
    'research assistant',
    'ux intern',
    'user research intern',
    'data analyst',
    'product design intern'
]
JOBBANK_SEARCH_LOCATIONS = [
    ONTARIO_SEARCH_LOCATION,
    'Toronto',
    'Mississauga',
    'Ottawa'
]
FAST_MODE = os.getenv("SCRAPE_FAST_MODE", "1") == "1"
REQUEST_TIMEOUT = float(os.getenv("SCRAPE_REQUEST_TIMEOUT", "4.5"))
TOTAL_SCRAPE_SECONDS = float(os.getenv("SCRAPE_TOTAL_TIMEOUT", "45"))
SOURCE_BUDGET_SECONDS = float(os.getenv("SCRAPE_SOURCE_TIMEOUT", "12"))
FAST_SOURCE_JOB_TARGET = int(os.getenv("SCRAPE_SOURCE_JOB_TARGET", "24"))
PARALLEL_SOURCES = os.getenv("SCRAPE_PARALLEL_SOURCES", "1") == "1"

_jobbank_terms_override = [
    term.strip() for term in os.getenv("JOBBANK_SEARCH_TERMS", "").split(",")
    if term.strip()
]
if _jobbank_terms_override:
    JOBBANK_SEARCH_TERMS = _jobbank_terms_override

_jobbank_locations_override = [
    location.strip() for location in os.getenv("JOBBANK_SEARCH_LOCATIONS", "").split(",")
    if location.strip()
]
if _jobbank_locations_override:
    JOBBANK_SEARCH_LOCATIONS = _jobbank_locations_override


def _sleep_short(delay_normal=0.3):
    """Use tiny pacing delays in fast mode to reduce end-to-end runtime."""
    time.sleep(0.05 if FAST_MODE else delay_normal)


def _source_budget_reached(started_at):
    """Prevent a single source from consuming the full scrape budget."""
    return FAST_MODE and (time.time() - started_at) >= SOURCE_BUDGET_SECONDS

def get_scraper_stats():
    """Get scraping statistics"""
    return _stats.get_summary()

def randomize_jobs(jobs):
    """Preserve deterministic ordering for stable scrape results."""
    return jobs or []


def is_student_opportunity(title, description=""):
    """Return True if posting appears student/entry-level focused."""
    text = f"{title} {description}".lower()
    student_keywords = [
        'intern', 'internship', 'student', 'new grad',
        'graduate', 'entry level', 'entry-level', 'junior', 'trainee',
        'apprentice', 'campus', 'recent graduate'
    ]
    return any(k in text for k in student_keywords)


def is_senior_or_high_level(title, description=""):
    """Return True if posting appears senior/high-level or explicitly full-time."""
    text = f"{title} {description}".lower()
    exclude_keywords = [
        'senior', 'sr.', 'lead', 'manager', 'director', 'principal', 'staff',
        'head of', 'vp', 'vice president', 'executive', 'mid-senior',
        '10+ years', '8+ years', '5+ years', 'full time', 'full-time',
        'co-op', 'coop', 'co op'
    ]
    return any(k in text for k in exclude_keywords)


def include_student_job(title, description=""):
    """Strict student-only inclusion filter."""
    return is_student_opportunity(title, description) and not is_senior_or_high_level(title, description)


def include_student_or_entry_context(title, description="", query_context=""):
    """Fallback inclusion for indexed/search-derived listings with sparse metadata."""
    if is_senior_or_high_level(title, description):
        return False
    if include_student_job(title, description):
        return True

    context = f"{title} {description} {query_context}".lower()
    entry_keywords = [
        'intern', 'internship', 'student', 'new grad', 'entry level',
        'entry-level', 'junior', 'recent graduate', 'graduate'
    ]
    return any(k in context for k in entry_keywords)


def infer_role(title, description=""):
    """Infer job role bucket from title/description for better role balance in UI."""
    text = f"{title} {description}".lower()

    uiux_keywords = ['ux', 'ui', 'product design', 'interaction design', 'visual design', 'designer']
    research_keywords = ['research', 'user study', 'usability', 'qualitative', 'quantitative']
    analyst_keywords = ['analyst', 'analysis', 'business intelligence', 'data']

    if any(k in text for k in uiux_keywords):
        return 'UI/UX'
    if any(k in text for k in research_keywords):
        return 'Research'
    if any(k in text for k in analyst_keywords):
        return 'Analyst'
    # Avoid analyst-heavy fallback when role cannot be inferred reliably.
    return 'Research'

def get_brave_driver():
    """Get webdriver for Brave browser only."""
    try:
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service as ChromeService
        from webdriver_manager.chrome import ChromeDriverManager

        brave_paths = [
            "C:\\Program Files\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
            "C:\\Program Files (x86)\\BraveSoftware\\Brave-Browser\\Application\\brave.exe",
        ]

        brave_binary = None
        for path in brave_paths:
            if os.path.exists(path):
                brave_binary = path
                break

        if not brave_binary:
            print("  [Browser Bot] Brave browser not found. Please install Brave.")
            return None

        options = webdriver.ChromeOptions()
        options.binary_location = brave_binary
        headless = os.getenv("BROWSER_HEADLESS", "1") == "1"
        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--window-size=1920,1080')
            options.add_argument('--disable-gpu')
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--no-sandbox')
        options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
        if not headless:
            options.add_argument('--start-maximized')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)

        service = ChromeService(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)

        driver.set_page_load_timeout(25)
        print(f"  [Browser Bot] Using Brave browser ({'headless' if headless else 'visible'})")
        return driver
    except Exception as e:
        print(f"  [Browser Bot] Could not initialize browser driver: {str(e)[:120]}")
        return None


def scrape_indeed_api():
    """Scrape STUDENT and entry-level jobs from Indeed web search pages."""
    try:
        print("  [Indeed Web] Searching Indeed job pages...")
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-CA,en;q=0.9'
        }

        # Target student-oriented terms with balanced role coverage.
        search_terms = ENTRY_LEVEL_SEARCH_TERMS
        locations = [ONTARIO_SEARCH_LOCATION]

        jobs = []
        seen = set()
        started_at = time.time()

        # First try Indeed RSS feeds (fast and stable).
        rss_terms = search_terms[:4] if FAST_MODE else search_terms[:6]
        for term in rss_terms:
            if _source_budget_reached(started_at):
                break
            for location in locations:
                if _source_budget_reached(started_at):
                    break
                rss_url = f"https://ca.indeed.com/rss?q={quote_plus(term)}&l={quote_plus(location)}&sort=date"
                try:
                    rss_resp = requests.get(rss_url, headers=headers, timeout=REQUEST_TIMEOUT)
                    if rss_resp.status_code == 200:
                        rss_soup = BeautifulSoup(rss_resp.text, 'xml')
                        for item in rss_soup.find_all('item')[:12]:
                            title = (item.title.text if item.title else '').strip()
                            job_url = (item.link.text if item.link else '').strip()
                            company = (item.find('source').text if item.find('source') else 'Unknown Company').strip()
                            description = (item.description.text if item.description else f"Indeed listing for {title}").strip()

                            if not title or not job_url:
                                continue

                            is_student = include_student_or_entry_context(title, description, term)

                            if not is_student:
                                continue

                            key = (title.lower().strip(), company.lower().strip(), job_url.lower().strip())
                            if key in seen:
                                continue
                            seen.add(key)

                            jobs.append({
                                "title": title[:100],
                                "company": company[:80],
                                "location": location[:80],
                                "role": infer_role(f"{title} {term}", description),
                                "description": BeautifulSoup(description, 'html.parser').get_text(" ", strip=True)[:300],
                                "url": job_url,
                                "posted_date": datetime.now().isoformat(),
                                "is_student_job": 1 if is_student else 0,
                                "source": "Indeed RSS"
                            })
                            if FAST_MODE and len(jobs) >= FAST_SOURCE_JOB_TARGET:
                                return randomize_jobs(jobs)
                except Exception:
                    pass

        # If RSS produced nothing, fall back to a small set of HTML pages.
        html_terms = search_terms[:3] if FAST_MODE else search_terms[:5]
        page_starts = [0, 10] if FAST_MODE else [0, 10, 20]
        for term in html_terms:
            if _source_budget_reached(started_at):
                break
            for location in locations:
                if _source_budget_reached(started_at):
                    break
                for start in page_starts:
                    if _source_budget_reached(started_at):
                        break
                    query = quote_plus(term)
                    loc = quote_plus(location)
                    url = f"https://ca.indeed.com/jobs?q={query}&l={loc}&sort=date&fromage=30&start={start}"

                    try:
                        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                        if response.status_code != 200:
                            continue

                        soup = BeautifulSoup(response.text, 'html.parser')
                        cards = soup.select('div.job_seen_beacon')
                        if not cards:
                            cards = soup.select('div.slider_container div[data-jk]')

                        for card in cards:
                            title_elem = card.select_one('h2.jobTitle a') or card.select_one('a.jcs-JobTitle')
                            if not title_elem:
                                continue

                            title = title_elem.get_text(strip=True)
                            href = title_elem.get('href', '')
                            if not href:
                                continue

                            job_url = href if href.startswith('http') else f"https://ca.indeed.com{href}"
                            company_elem = card.select_one('[data-testid="company-name"]') or card.select_one('span.companyName')
                            company = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'

                            location_elem = card.select_one('[data-testid="text-location"]') or card.select_one('div.companyLocation')
                            job_location = location_elem.get_text(strip=True) if location_elem else location

                            snippet_elem = card.select_one('[data-testid="job-snippet"]') or card.select_one('div.job-snippet')
                            description = snippet_elem.get_text(" ", strip=True) if snippet_elem else f"Indeed listing for {title}"

                            is_student = include_student_or_entry_context(title, description, term)

                            if not is_student:
                                continue

                            key = (title.lower().strip(), company.lower().strip(), job_url.lower().strip())
                            if key in seen:
                                continue
                            seen.add(key)

                            jobs.append({
                                "title": title[:100],
                                "company": company[:80],
                                "location": job_location[:80],
                                "role": infer_role(f"{title} {term}", description),
                                "description": description[:300],
                                "url": job_url,
                                "posted_date": datetime.now().isoformat(),
                                "is_student_job": 1 if is_student else 0,
                                "source": "Indeed Web"
                            })
                            if FAST_MODE and len(jobs) >= FAST_SOURCE_JOB_TARGET:
                                return randomize_jobs(jobs)

                    except Exception:
                        continue

                    # Avoid hammering Indeed.
                    _sleep_short(0.3)

        if jobs:
            print(f"      Found {len(jobs)} real Indeed jobs")
            jobs = randomize_jobs(jobs)
            print(f"      Returning {len(jobs)} randomized jobs")
            return jobs

    except Exception as e:
        print(f"      [Indeed Web] Error: {str(e)[:100]}")

    return []


def scrape_linkedin_api():
    """Scrape STUDENT and entry-level jobs from LinkedIn"""
    try:
        print("  [LinkedIn] Searching for student/internship opportunities...")
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        }
        target_cities = ['Ottawa', 'Kitchener', 'Waterloo', 'Guelph', 'Mississauga', 'Toronto']
        jobs = []
        seen = set()

        if jobs:
            print(f"      Found {len(jobs)} jobs")
            jobs = randomize_jobs(jobs)
            print(f"      Returning {len(jobs)} randomized jobs")
            return jobs
    except Exception as e:
        pass
    
    return []


def scrape_indeed_via_search_index():
    """Fallback: discover live Indeed posting URLs through search index pages."""
    try:
        print("  [Indeed Index Bot] Searching indexed Indeed postings...")
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-CA,en;q=0.9'
        }

        queries = [
            'site:ca.indeed.com/viewjob ux intern ontario',
            'site:ca.indeed.com/viewjob junior analyst ontario',
            'site:ca.indeed.com/viewjob research intern ontario',
            'site:ca.indeed.com/viewjob entry level ontario',
            'site:ca.indeed.com/viewjob internship ontario',
            'site:ca.indeed.com/viewjob student ontario',
        ]

        jobs = []
        seen = set()
        started_at = time.time()
        for q in queries:
            if _source_budget_reached(started_at):
                break
            ddg_url = f"https://duckduckgo.com/html/?q={quote_plus(q)}"
            try:
                response = requests.get(ddg_url, headers=headers, timeout=REQUEST_TIMEOUT)
                if response.status_code != 200:
                    continue

                soup = BeautifulSoup(response.text, 'html.parser')
                for result in soup.select('a.result__a')[:12]:
                    title = result.get_text(strip=True)
                    href = result.get('href', '')
                    if not href:
                        continue

                    # DuckDuckGo redirect format: /l/?uddg=<encoded_url>
                    if 'uddg=' in href:
                        href = unquote(href.split('uddg=')[-1].split('&')[0])

                    if 'indeed.com/viewjob' not in href:
                        continue

                    key = (title.lower().strip(), href.lower().strip())
                    if key in seen:
                        continue
                    seen.add(key)

                    is_student = include_student_or_entry_context(title, "", q)

                    if not is_student:
                        continue

                    jobs.append({
                        "title": title[:100],
                        "company": "Indeed Employer",
                        "location": ONTARIO_SEARCH_LOCATION,
                        "role": infer_role(title, ""),
                        "description": "Indexed Indeed posting discovered by search bot.",
                        "url": href,
                        "posted_date": datetime.now().isoformat(),
                        "is_student_job": 1 if is_student else 0,
                        "source": "Indeed Index Bot"
                    })
                    if FAST_MODE and len(jobs) >= FAST_SOURCE_JOB_TARGET:
                        return randomize_jobs(jobs)
            except Exception:
                continue

            _sleep_short(0.3)

        if jobs:
            print(f"      Found {len(jobs)} indexed Indeed jobs")
            return randomize_jobs(jobs)

    except Exception as e:
        print(f"      [Indeed Index Bot] Error: {str(e)[:100]}")

    return []


def scrape_board_via_search_index(board_name, domain, target_cities=None):
    """Fallback: discover live posting URLs for a board via search index pages."""
    try:
        print(f"  [{board_name} Index Bot] Searching indexed {board_name} postings...")
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-CA,en;q=0.9'
        }

        cities = target_cities if target_cities else TARGET_CITIES
        terms = ['ux intern', 'research intern', 'junior analyst', 'entry level', 'student']
        if board_name.lower() == 'jobbank':
            # JobBank uses broader search terms
            cities = target_cities if target_cities else TARGET_CITIES
            terms = ['intern', 'entry level', 'junior']

        jobs = []
        seen = set()
        started_at = time.time()

        terms_to_use = terms
        for city in cities:
            if _source_budget_reached(started_at):
                break
            for term in terms_to_use:
                if _source_budget_reached(started_at):
                    break
                q = f"site:{domain} {term} {city} ON"
                ddg_url = f"https://duckduckgo.com/html/?q={quote_plus(q)}"
                try:
                    response = requests.get(ddg_url, headers=headers, timeout=REQUEST_TIMEOUT)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')
                    for result in soup.select('a.result__a')[:8]:
                        title = result.get_text(strip=True)
                        href = result.get('href', '')
                        if not href:
                            continue

                        if 'uddg=' in href:
                            href = unquote(href.split('uddg=')[-1].split('&')[0])

                        if domain not in href:
                            continue

                        clean_title = title.strip()
                        if not clean_title or not include_student_or_entry_context(clean_title, "", f"{term} {city}"):
                            continue

                        key = (clean_title.lower().strip(), href.lower().strip())
                        if key in seen:
                            continue
                        seen.add(key)

                        jobs.append({
                            "title": clean_title[:100],
                            "company": f"{board_name} Employer",
                            "location": city,
                            "role": infer_role(clean_title, term),
                            "description": f"Indexed {board_name} posting discovered by search bot.",
                            "url": href,
                            "posted_date": datetime.now().isoformat(),
                            "is_student_job": 1,
                            "source": f"{board_name} Index Bot"
                        })
                        if FAST_MODE and len(jobs) >= FAST_SOURCE_JOB_TARGET:
                            return randomize_jobs(jobs)
                except Exception:
                    continue

                _sleep_short(0.2)

        if jobs:
            print(f"      Found {len(jobs)} indexed {board_name} jobs")
            return randomize_jobs(jobs)

    except Exception as e:
        print(f"      [{board_name} Index Bot] Error: {str(e)[:100]}")

    return []


def scrape_workopolis():
    """Scrape STUDENT and entry-level jobs from Workopolis (Canadian job board)."""
    try:
        print("  [Workopolis] Searching Workopolis job pages...")
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-CA,en;q=0.9'
        }

        # Run Workopolis with one query across the requested six cities.
        search_terms = [WORKOPOLIS_QUERY]
        locations = WORKOPOLIS_TARGET_CITIES

        jobs = []
        seen = set()
        started_at = time.time()

        # Try Workopolis search pages
        terms_to_use = search_terms
        for term in terms_to_use:
            if _source_budget_reached(started_at):
                break
            for location in locations:
                if _source_budget_reached(started_at):
                    break
                # Workopolis search URL format
                query = quote_plus(term)
                loc = quote_plus(location)
                url = f"https://www.workopolis.com/jobsearch?keyword={query}&location={loc}&sort=date"

                try:
                    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')
                    
                    # Workopolis uses various selectors for job cards
                    job_cards = soup.select('div[data-test-id="JobCard"]')
                    if not job_cards:
                        job_cards = soup.select('div.JobCard')
                    if not job_cards:
                        job_cards = soup.select('article.job-item')

                    for card in job_cards[:15]:
                        try:
                            # Extract title
                            title_elem = card.select_one('a[data-qa="JobTitle"]') or \
                                        card.select_one('h2 a') or \
                                        card.select_one('span.job-title')
                            if not title_elem:
                                continue

                            title = title_elem.get_text(strip=True)
                            href = title_elem.get('href', '')
                            
                            if not href:
                                continue

                            job_url = href if href.startswith('http') else f"https://www.workopolis.com{href}"

                            # Extract company
                            company_elem = card.select_one('span[data-qa="JobCompany"]') or \
                                          card.select_one('a[data-qa="JobCompanyLink"]') or \
                                          card.select_one('span.job-company')
                            company = company_elem.get_text(strip=True) if company_elem else 'Unknown Company'

                            # Extract location (Workopolis might have it in the card)
                            job_location = location
                            location_elem = card.select_one('span[data-qa="JobLocation"]') or \
                                           card.select_one('span.job-location')
                            if location_elem:
                                job_location = location_elem.get_text(strip=True)

                            # Extract description/snippet
                            snippet_elem = card.select_one('p.job-snippet') or \
                                          card.select_one('span.job-description') or \
                                          card.select_one('p[data-qa="JobDescription"]')
                            description = snippet_elem.get_text(" ", strip=True) if snippet_elem else f"Workopolis listing for {title}"

                            # Apply the same student/entry-level filter used by Indeed.
                            is_student = include_student_or_entry_context(title, description, term)

                            if not is_student:
                                continue

                            key = (title.lower().strip(), company.lower().strip(), job_url.lower().strip())
                            if key in seen:
                                continue
                            seen.add(key)

                            jobs.append({
                                "title": title[:100],
                                "company": company[:80],
                                "location": job_location[:80],
                                "role": infer_role(f"{title} {term}", description),
                                "description": description[:300],
                                "url": job_url,
                                "posted_date": datetime.now().isoformat(),
                                "is_student_job": 1 if is_student else 0,
                                "source": "Workopolis"
                            })
                            if FAST_MODE and len(jobs) >= FAST_SOURCE_JOB_TARGET:
                                return randomize_jobs(jobs)
                        except Exception:
                            continue

                except Exception:
                    continue

                # Avoid hammering Workopolis
                _sleep_short(0.3)

        if jobs:
            print(f"      Found {len(jobs)} jobs on Workopolis")
            jobs = randomize_jobs(jobs)
            print(f"      Returning {len(jobs)} randomized jobs")
            return jobs

    except Exception as e:
        print(f"      [Workopolis] Error: {str(e)[:100]}")

    return []


def get_sample_jobs_for_demo():
    """No sample data. Return empty list to enforce real job fetching."""
    return []


def scrape_with_brave_browser(target_cities=None):
    """Use a real browser bot for advanced Indeed scraping, optionally across specific cities."""
    try:
        driver = get_brave_driver()
        if not driver:
            return []
        
        print("  [Browser Bot] Using automated browser to scrape Indeed...")
        jobs = []
        seen = set()
        cities = target_cities if target_cities else WORKOPOLIS_TARGET_CITIES
        
        try:
            from selenium.webdriver.common.by import By
            from selenium.webdriver.support.ui import WebDriverWait
            from selenium.webdriver.support import expected_conditions as EC
            city_queries = [
                'ux intern',
                'research intern',
                'junior analyst',
                'entry level designer',
                'entry level researcher'
            ]
            if FAST_MODE:
                city_queries = city_queries[:2]

            for city in cities:
                for q in city_queries:
                    query_city = quote_plus(ONTARIO_SEARCH_LOCATION)
                    query_role = quote_plus(q)
                    driver.get(f"https://ca.indeed.com/jobs?q={query_role}&l={query_city}&sort=date&fromage=14")
                    time.sleep(1.0 if FAST_MODE else 2.0)

                    # Wait for job listings
                    try:
                        job_cards = WebDriverWait(driver, 4 if FAST_MODE else 8).until(
                            EC.presence_of_all_elements_located((By.CLASS_NAME, "job_seen_beacon"))
                        )
                    except Exception:
                        job_cards = driver.find_elements(By.CSS_SELECTOR, "div.job_seen_beacon, div.slider_container div[data-jk]")

                    print(f"  [Browser Bot] {city} / {q}: Found {len(job_cards)} job listings")

                    # Extract job information
                    for card in job_cards[:6 if FAST_MODE else 10]:
                        try:
                            try:
                                title_elem = card.find_element(By.XPATH, ".//h2/a")
                            except Exception:
                                title_elem = card.find_element(By.CSS_SELECTOR, "a.jcs-JobTitle")
                            title = title_elem.text
                            url = title_elem.get_attribute("href")

                            if not url.startswith("http"):
                                url = "https://ca.indeed.com" + url

                            try:
                                company_elem = card.find_element(By.XPATH, ".//*[@data-testid='company-name']")
                                company = company_elem.text
                            except Exception:
                                try:
                                    company = card.find_element(By.CSS_SELECTOR, "span.companyName").text
                                except Exception:
                                    company = "Unknown"

                            is_student = include_student_job(title, q)

                            if not is_student:
                                continue

                            key = (title.lower().strip(), company.lower().strip(), url.lower().strip())
                            if key in seen:
                                continue
                            seen.add(key)

                            jobs.append({
                                "title": title[:100],
                                "company": company[:80],
                                "location": ONTARIO_SEARCH_LOCATION,
                                "role": infer_role(title, q),
                                "description": "From Indeed",
                                "url": url,
                                "posted_date": datetime.now().isoformat(),
                                "is_student_job": 1 if is_student else 0,
                                "source": "Indeed (Brave Browser)"
                            })
                        except Exception:
                            pass

                # If Indeed presents a security challenge, allow a short window.
                if "security check" in driver.title.lower():
                    headless = os.getenv("BROWSER_HEADLESS", "1") == "1"
                    if headless:
                        print("  [Browser Bot] Indeed security check detected in headless mode; waiting briefly before continuing...")
                    else:
                        print("  [Browser Bot] Indeed security check detected. Complete it in browser if prompted...")
                    for _ in range(6 if FAST_MODE else 20):
                        time.sleep(1)
                        if "security check" not in driver.title.lower():
                            break
            
            if jobs:
                print(f"  [Browser Bot] Extracted {len(jobs)} jobs from Indeed browser session")
            return jobs
        
        finally:
            try:
                driver.quit()
            except Exception:
                pass
    
    except Exception as e:
        print(f"  [Browser Bot] Browser scraping failed: {str(e)[:80]}")
        return []


def scrape_jobbank():
    """Scrape entry-level and student jobs from Job Bank (Canada's national job board)."""
    try:
        print("  [JobBank] Searching Job Bank job pages...")
        from bs4 import BeautifulSoup

        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept-Language': 'en-CA,en;q=0.9'
        }

        # Use the Ontario search URL format that Job Bank currently serves.
        search_terms = JOBBANK_SEARCH_TERMS[:8] if FAST_MODE else JOBBANK_SEARCH_TERMS

        jobs = []
        seen = set()
        started_at = time.time()

        for term in search_terms:
            if _source_budget_reached(started_at):
                break
            query = quote_plus(term)
            for location in JOBBANK_SEARCH_LOCATIONS:
                if _source_budget_reached(started_at):
                    break

                loc = quote_plus(location)
                url = f"https://www.jobbank.gc.ca/jobsearch/jobsearch?searchstring={query}&locationstring={loc}&locationparam="

                try:
                    response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
                    if response.status_code != 200:
                        continue

                    soup = BeautifulSoup(response.text, 'html.parser')

                    # Modern Job Bank search results use resultJobItem anchors inside resultJobItem articles.
                    job_cards = soup.select('a.resultJobItem')
                    if not job_cards:
                        job_cards = soup.select('article.action-buttons > a[href*="/jobposting/"]')
                    if not job_cards:
                        job_cards = soup.select('.results-jobs a[href*="/jobposting/"]')

                    for card in job_cards[:25]:
                        try:
                            title_elem = card.select_one('h3.title .noctitle') or card.select_one('h3.title') or card.select_one('.noctitle')
                            if not title_elem:
                                continue

                            title = title_elem.get_text(" ", strip=True)
                            href = card.get('href', '')
                            if not title or not href:
                                continue

                            job_url = href if href.startswith('http') else f"https://www.jobbank.gc.ca{href}"
                            job_id_match = re.search(r'/jobposting/(\d+)', job_url)
                            job_fingerprint = job_id_match.group(1) if job_id_match else job_url.lower().strip()

                            company_elem = card.select_one('li.business') or card.select_one('.business')
                            company = company_elem.get_text(" ", strip=True) if company_elem else 'Unknown Company'

                            location_elem = card.select_one('li.location') or card.select_one('.location')
                            job_location = location_elem.get_text(" ", strip=True) if location_elem else location

                            description = card.get_text(" ", strip=True)

                            # Apply student/entry-level filter.
                            is_student = include_student_or_entry_context(title, description, term)
                            if not is_student:
                                continue

                            key = (title.lower().strip(), company.lower().strip(), job_fingerprint)
                            if key in seen:
                                continue
                            seen.add(key)

                            jobs.append({
                                "title": title[:100],
                                "company": company[:80],
                                "location": job_location[:80],
                                "role": infer_role(f"{title} {term}", description),
                                "description": description[:300],
                                "url": job_url,
                                "posted_date": datetime.now().isoformat(),
                                "is_student_job": 1 if is_student else 0,
                                "source": "Job Bank"
                            })
                            if FAST_MODE and len(jobs) >= FAST_SOURCE_JOB_TARGET:
                                return randomize_jobs(jobs)
                        except Exception:
                            continue

                except Exception:
                    continue

                # Avoid hammering Job Bank
                _sleep_short(0.3)

        if jobs:
            print(f"      Found {len(jobs)} jobs on Job Bank")
            jobs = randomize_jobs(jobs)
            print(f"      Returning {len(jobs)} randomized jobs")
            return jobs

    except Exception as e:
        print(f"      [JobBank] Error: {str(e)[:100]}")

    return []


def scrape_all_browser_jobs():
    """Scrape STUDENT jobs from Indeed and Workopolis only."""
    print("\n" + "=" * 60)
    print("STUDENT JOB SCRAPING - ENTRY LEVEL & INTERNSHIPS ONLY")
    print("=" * 60)
    print("Searching for student opportunities and internships...")
    
    _stats.start()
    all_jobs = []
    
    # Run primary sources (Indeed + JobBank) with a hard overall time budget.
    scrape_start = time.time()
    source_jobs = {
        "Indeed API": lambda: scrape_indeed_api(),
        "JobBank": lambda: scrape_jobbank(),
    }

    if PARALLEL_SOURCES:
        print("\n[1/5] Running primary sources in parallel...")
        executor = ThreadPoolExecutor(max_workers=2)
        futures = {executor.submit(fn): name for name, fn in source_jobs.items()}
        try:
            remaining_budget = max(1.0, TOTAL_SCRAPE_SECONDS - (time.time() - scrape_start))
            for future in as_completed(futures, timeout=remaining_budget):
                name = futures[future]
                try:
                    jobs = future.result() or []
                    all_jobs.extend(jobs)
                    _stats.record_source(name, len(jobs))
                    print(f"[{name}] Completed with {len(jobs)} jobs")
                except Exception as e:
                    _stats.record_error(name, e)
                    print(f"[✗] {name} error: {str(e)[:80]}")
        except TimeoutError:
            print("[!] Primary source parallel budget reached; continuing with available results")
            for future, name in futures.items():
                if not future.done():
                    future.cancel()
                elif name not in _stats.jobs_found:
                    try:
                        jobs = future.result() or []
                        all_jobs.extend(jobs)
                        _stats.record_source(name, len(jobs))
                    except Exception as e:
                        _stats.record_error(name, e)
        finally:
            executor.shutdown(wait=False, cancel_futures=True)
    else:
        print("\n[1/5] Running primary sources sequentially (safe mode)...")
        for name, fn in source_jobs.items():
            try:
                jobs = fn() or []
                all_jobs.extend(jobs)
                _stats.record_source(name, len(jobs))
                print(f"[{name}] Completed with {len(jobs)} jobs")
            except Exception as e:
                _stats.record_error(name, e)
                print(f"[✗] {name} error: {str(e)[:80]}")

    _stats.record_source("LinkedIn", 0)
    _stats.record_source("Glassdoor", 0)
    
    # Remove duplicates and keep strictly student-only valid jobs
    unique_jobs = []
    seen = set()
    for job in all_jobs:
        key = (job.get('title', '').lower().strip(), job.get('url', '').lower().strip())
        title = job.get('title', '')
        description = job.get('description', '')
        is_student = job.get('is_student_job', 0) == 1
        if key not in seen and job.get('url') and is_student and include_student_job(title, description):
            unique_jobs.append(job)
            seen.add(key)
    
    # If no real jobs found, try indexed Indeed bot
    if not unique_jobs:
        print("\n[5/5] Indeed direct blocked, trying indexed Indeed bot...")
        try:
            indexed_jobs = scrape_indeed_via_search_index()
            unique_jobs.extend(indexed_jobs)
            _stats.record_source("Indeed Index Bot", len(indexed_jobs))
        except Exception as e:
            _stats.record_error("Indeed Index Bot", e)
            print(f"[✗] Indexed Indeed bot error: {str(e)[:80]}")

    use_browser_fallback = os.getenv("ENABLE_BROWSER_FALLBACK", "0") == "1"

    # Keep fallback path lightweight: use search index first for missing cities,
    # then use browser fallback only if results are still too low.
    present_cities = {str(j.get('location', '')).split(',')[0].strip() for j in unique_jobs if j.get('location')}
    missing_cities = [city for city in TARGET_CITIES if city not in present_cities]

    if missing_cities:
        print(f"\n[6/5] Filling missing cities via indexed sources: {', '.join(missing_cities)}")
        try:
            indexed_workopolis = scrape_board_via_search_index("Workopolis", "workopolis.com", target_cities=missing_cities)
            indexed_indeed = scrape_indeed_via_search_index()
            unique_jobs.extend(indexed_workopolis)
            unique_jobs.extend(indexed_indeed)
            _stats.record_source("Indexed Fallback", len(indexed_workopolis) + len(indexed_indeed))
        except Exception as e:
            _stats.record_error("Indexed Fallback", e)
            print(f"[✗] Indexed fallback error: {str(e)[:80]}")

    if use_browser_fallback and len(unique_jobs) < 15:
        print(f"\n[7/5] Results still low ({len(unique_jobs)}). Running browser fallback...")
        try:
            cities_for_browser = missing_cities if missing_cities else TARGET_CITIES[:4]
            wp_browser = scrape_workopolis_with_brave_browser(target_cities=cities_for_browser)
            indeed_browser = scrape_with_brave_browser(target_cities=cities_for_browser)
            unique_jobs.extend(wp_browser)
            unique_jobs.extend(indeed_browser)
            _stats.record_source("Browser Fallback", len(wp_browser) + len(indeed_browser))
        except Exception as e:
            _stats.record_error("Browser Fallback", e)
            print(f"[✗] Browser fallback error: {str(e)[:80]}")
    
    # No fallback to sample data - report that no jobs were found
    if not unique_jobs:
        print("\n[!] No jobs found from any source")
        print("    Please check:")
        print("    - Internet connection (ping google.com)")
        print("    - API accessibility")
        print("    - Firewall/proxy settings")
    
    _stats.end()
    
    # Final randomization - shuffle all results
    unique_jobs = randomize_jobs(unique_jobs)
    
    print("\n" + "=" * 60)
    print(f"Total jobs found: {len(unique_jobs)}")
    stats_summary = _stats.get_summary()
    print(f"Time taken: {stats_summary['duration_seconds']:.2f} seconds")
    print(f"Sources succeeded: {stats_summary['sources_succeeded']}")
    print(f"Sources failed: {stats_summary['sources_failed']}")
    print("=" * 60 + "\n")
    
    return unique_jobs


if __name__ == "__main__":
    jobs = scrape_all_browser_jobs()
    print(f"Total jobs: {len(jobs)}")
    for job in jobs[:5]:
        print(f"  - {job['title']} @ {job['company']}")
