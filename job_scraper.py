"""
Job Scraper Module
Fetches job listings from free public job APIs
Filters by keywords (UI/UX, Research, Analyst) and Ontario locations
"""

import requests
from datetime import datetime
import time

# Keywords to search for
KEYWORDS = ['UX', 'UI', 'Designer', 'Research', 'Analyst', 'Data Analyst', 
            'Business Analyst', 'Product Manager', 'Product Designer']

# Locations to filter for (Ontario only)
ONTARIO_LOCATIONS = ['Ontario', 'Toronto', 'Ottawa', 'Mississauga', 'Guelph', 'Canada', 'Remote']


class JobScraper:
    """Base job scraper class"""
    
    def __init__(self, timeout=15):
        self.timeout = timeout
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
    
    def matches_keywords(self, text):
        """Check if text contains any of the target keywords"""
        if not text:
            return False
        text_lower = text.lower()
        return any(keyword.lower() in text_lower for keyword in KEYWORDS)
    
    def matches_location(self, text):
        """Check if text contains Ontario or is remote"""
        if not text:
            return True  # Include jobs with no location specified
        text_lower = text.lower()
        return any(loc.lower() in text_lower for loc in ONTARIO_LOCATIONS)


class RemoteOKScraper(JobScraper):
    """Fetches jobs from RemoteOK API - free, no auth required"""
    
    def fetch_jobs(self):
        """
        Fetches remote jobs from RemoteOK
        """
        jobs = []
        
        try:
            print('Fetching jobs from RemoteOK API...')
            
            url = 'https://remoteok.io/api'
            response = requests.get(url, headers=self.headers, timeout=self.timeout)
            response.raise_for_status()
            
            data = response.json()
            print(f'  Got {len(data)} total jobs from RemoteOK')
            
            for job_data in data[:100]:  # Check first 100
                try:
                    # Skip if removed
                    if job_data.get('id') == 'removed' or not job_data.get('id'):
                        continue
                    
                    title = job_data.get('title', '').strip()
                    company = job_data.get('company', '').strip()
                    location = job_data.get('location', 'Remote').strip()
                    job_url = job_data.get('url', '').strip()
                    tags = job_data.get('tags', [])
                    
                    # Skip if missing key fields
                    if not title or not company or not job_url:
                        continue
                    
                    # Check keywords in title
                    title_matches = self.matches_keywords(title)
                    
                    # Check keywords in tags
                    tags_str = ' '.join(tags) if isinstance(tags, list) else str(tags)
                    tags_match = self.matches_keywords(tags_str)
                    
                    # Include if matches keywords and is remote
                    if (title_matches or tags_match) and 'remote' in location.lower():
                        job = {
                            'title': title,
                            'company': company,
                            'location': location,
                            'role': title.split('-')[0].strip() if '-' in title else 'Remote Job',
                            'description': job_data.get('description', ''),
                            'url': job_url,
                            'posted_date': datetime.now().isoformat()
                        }
                        jobs.append(job)
                        print(f'  ? {title}')
                        
                except Exception as e:
                    continue
            
        except Exception as e:
            print(f'RemoteOK error:  {str(e)}')
        
        return jobs


class JoobleAPIScraper(JobScraper):
    """Fetches jobs from Jooble API - free public API"""
    
    def fetch_jobs(self):
        """
        Fetches jobs from Jooble API
        """
        jobs = []
        search_queries = [
            ('UX Designer', 'Ontario'),
            ('Data Analyst', 'Ontario'),
            ('Analyst', 'Ontario'),
            ('Product Manager', 'Ontario'),
            ('Research', 'Toronto')
        ]
        
        for keyword, location in search_queries:
            try:
                print(f'Searching Jooble for {keyword} in {location}...')
                
                url = 'https://api.jooble.org/api/search'
                payload = {
                    'keywords': keyword,
                    'location': location,
                    'page': 1
                }
                
                response = requests.post(url, json=payload, timeout=self.timeout)
                response.raise_for_status()
                data = response.json()
                
                if 'jobs' in data:
                    print(f'  Found {len(data.get("jobs", []))} jobs')
                    
                    for job_data in data['jobs'][:15]:
                        try:
                            title = job_data.get('title', '').strip()
                            company = job_data.get('company', '').strip()
                            location_job = job_data.get('location', 'Canada').strip()
                            job_url = job_data.get('link', '').strip()
                            
                            if not title or not company:
                                continue
                            
                            # Only include Ontario/Toronto jobs or check if keyword matches
                            if self.matches_keywords(title):
                                job = {
                                    'title': title,
                                    'company': company,
                                    'location': location_job,
                                    'role': keyword,
                                    'description': job_data.get('snippet', ''),
                                    'url': job_url,
                                    'posted_date': datetime.now().isoformat()
                                }
                                jobs.append(job)
                                print(f'  ? {title} at {company}')
                        except Exception as e:
                            continue
                
                import time
                time.sleep(1)  # Be respectful with API
                
            except Exception as e:
                print(f'Jooble error for {keyword}:  {str(e)}')
                continue
        
        return jobs


def scrape_all_jobs():
    """
    Master function to scrape all job sources
    Returns all jobs matching target keywords
    """
    all_jobs = []
    
    print('=' * 70)
    print('JOB SCRAPER - Fetching from public job APIs')
    print('=' * 70)
    
    # Try these scrapers in order
    scrapers = [
        JoobleAPIScraper(),      # Free API, most reliable
        RemoteOKScraper(),       # Free API for remote jobs
    ]
    
    for scraper in scrapers:
        try:
            print(f'\\n--- {scraper.__class__.__name__} ---')
            jobs = scraper.fetch_jobs()
            
            if jobs:
                all_jobs.extend(jobs)
                print(f'? {scraper.__class__.__name__}: Found {len(jobs)} jobs')
        except Exception as e:
            print(f'? {scraper.__class__.__name__} error: {str(e)}')
            continue
    
    print('\\n' + '=' * 70)
    print(f'? Total jobs found: {len(all_jobs)}')
    print('=' * 70)
    
    if all_jobs:
        print('\\nSample jobs found:')
        for i, job in enumerate(all_jobs[:3], 1):
            print(f'\\n  {i}. {job[\"title\"]}')
            print(f'     Company: {job[\"company\"]}')
            print(f'     Location: {job[\"location\"]}')
            print(f'     Link: {job[\"url\"]}')
    
    return all_jobs