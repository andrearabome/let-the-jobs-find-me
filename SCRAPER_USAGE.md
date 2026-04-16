# Scraper System Usage Guide

## Quick Start (2 minutes)

### 1. Install Dependencies
```bash
python setup_scraper.py
```

### 2. Run the App
```bash
python app.py
```

### 3. Fetch Jobs
- Go to http://localhost:5000
- Click "Fetch Jobs" button
- Wait 30-60 seconds
- Jobs appear in the list

## Your Scraper System

### Architecture

```
┌─────────────────────────────────────────────┐
│      Web Interface (Flask)                  │
│      http://localhost:5000                  │
└────────────────┬────────────────────────────┘
                 │
                 ↓
        ┌────────────────────┐
        │  app.py            │
        │  /api/scrape-jobs  │
        └────────┬───────────┘
                 │
                 ↓
   ┌─────────────────────────────────────────┐
   │   browser_scraper.py                    │
   │   (Main Scraping Engine)                │
   └──┬──────────────────┬────────────────┬──┘
      │                  │                │
      ↓                  ↓                ↓
   ┌──────────┐  ┌─────────────┐  ┌──────────────┐
   │ APIs     │  │ Browser     │  │ Sample Data  │
   │ (Fast)   │  │ (Fallback)  │  │ (Final)      │
   └──────────┘  └─────────────┘  └──────────────┘
      │                  │                │
      └──────┬───────────┴────────────────┘
             ↓
   ┌────────────────────────┐
   │  SQLite Database      │
   │  (jobs.db)            │
   └────────────────────────┘
```

### Data Flow

1. **Input**: Click "Fetch Jobs" in web interface
2. **Stage 1 - Fast APIs**: Try Indeed, LinkedIn, Glassdoor APIs
3. **Stage 2 - Browser**: If APIs fail, use Brave browser automation
4. **Stage 3 - Fallback**: If browser fails, use sample data
5. **Processing**: Deduplicate jobs, validate data
6. **Output**: Store in database, display in web interface

## Features

### ✨ Multi-Source Scraping
- **Indeed API**: Real-time job listings
- **LinkedIn**: Professional network jobs
- **Glassdoor**: Company reviews + jobs
- **Brave Browser**: Advanced web scraping
- **Sample Data**: Guaranteed data availability

### 🔄 Smart Fallbacks
- Automatic retry on error
- Multiple source redundancy
- Sample data as final fallback
- Status reporting

### 🎯 Intelligent Filtering
- Keyword matching (UX, Analyst, etc.)
- Location filtering (Ontario)
- Experience level detection (Entry/Intern)
- Duplicate removal

### 📊 Tracking & Analytics
- Source attribution
- Scraping statistics
- Error logging
- Performance metrics

## Configuration

### Basic Configuration

Edit `scraper_config.py`:

```python
# Keywords to search for
SEARCH_KEYWORDS = [
    'UX', 'UI', 'Designer',
    'Analyst', 'Research',
    'Product Manager'
]

# Locations
ONTARIO_LOCATIONS = [
    'Toronto', 'Ottawa', 'Kitchener', 'Remote'
]

# Timeouts
API_TIMEOUT = 15
BROWSER_TIMEOUT = 30
```

### Advanced Configuration

```python
# Rate limiting
DELAY_BETWEEN_REQUESTS = 1  # seconds

# Caching
ENABLE_CACHE = True
CACHE_DURATION = 3600  # 1 hour

# Limits
MAX_JOBS_PER_SOURCE = 25
MAX_RETRIES = 3
```

## Browser Setup (Optional)

### Install Brave Browser

**Windows:**
- Download: https://brave.com/download/
- Or: `choco install brave`

**macOS:**
```bash
brew install brave-browser
```

**Linux:**
```bash
sudo apt install brave-browser  # Ubuntu/Debian
```

### Verify Installation

```bash
# Windows PowerShell
where brave.exe

# macOS/Linux
which brave-browser
```

## Testing

### Quick Test
```bash
python test_scraper_suite.py --quick
```

### Full Test Suite
```bash
python test_scraper_suite.py
```

### Test Specific Components

```python
from browser_scraper import scrape_all_browser_jobs

# Test complete pipeline
jobs = scrape_all_browser_jobs()
print(f"Found {len(jobs)} jobs")

# Test sample data
from browser_scraper import get_sample_jobs_for_demo
jobs = get_sample_jobs_for_demo()
print(f"Sample jobs: {len(jobs)}")
```

## Troubleshooting

### ❌ "No jobs found"

**Check 1**: Internet connection
```bash
ping google.com
```

**Check 2**: API accessibility
```python
import requests
r = requests.get("https://ca.indeed.com", timeout=10)
print(r.status_code)
```

**Check 3**: Browser installed (if using Brave)
```bash
# Windows
Test-Path "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
```

### ❌ "Selenium not installed"

```bash
pip install selenium webdriver-manager
```

### ❌ "Timeout errors"

**Solution 1**: Increase timeout
```python
# In browser_scraper.py
response = requests.get(url, timeout=30)  # Increase timeout
```

**Solution 2**: Check internet speed
```bash
pip install speedtest-cli
speedtest-cli
```

### ❌ "Website blocked scraper"

**Try:**
1. Wait 5 minutes before retrying
2. Use VPN/proxy
3. Reduce scraping frequency
4. Use sample data

## Performance

### Typical Performance

| Metric | Value |
|--------|-------|
| API Scraping | 10-30 seconds |
| Browser Scraping | 30-60 seconds |
| Sample Data Load | <1 second |
| Deduplication | <1 second |
| Database Insert | 1-5 seconds |
| **Total** | **30-65 seconds** |

### Optimization Tips

1. **Use APIs first** (faster than browser)
2. **Cache results** (avoid re-scraping)
3. **Limit results** (fewer = faster)
4. **Parallel processing** (if supported)

## Database

### Job Schema

```sql
CREATE TABLE jobs (
    id INTEGER PRIMARY KEY,
    title TEXT,
    company TEXT,
    location TEXT,
    role TEXT,
    description TEXT,
    url TEXT,
    posted_date TEXT,
    salary TEXT,
    is_student_job INTEGER,
    source TEXT,  -- Which scraper found it
    created_at TIMESTAMP
);
```

### Query Examples

```sql
-- Get all analyst jobs
SELECT title, company, url FROM jobs 
WHERE title LIKE '%Analyst%'
ORDER BY created_at DESC;

-- Get student internships
SELECT * FROM jobs 
WHERE is_student_job = 1 
AND title LIKE '%Intern%';

-- Jobs by source
SELECT source, COUNT(*) as count 
FROM jobs 
GROUP BY source;

-- Recent jobs (last 7 days)
SELECT * FROM jobs 
WHERE created_at > datetime('now', '-7 days');
```

## API Endpoints

### Scrape Jobs (POST)

```bash
curl -X POST http://localhost:5000/api/scrape-jobs
```

**Response:**
```json
{
  "success": true,
  "imported": 15,
  "duplicates_skipped": 3,
  "total_found": 18,
  "message": "Successfully imported 15 new jobs"
}
```

### Get Jobs (GET)

```bash
# All jobs
curl http://localhost:5000/api/jobs

# Filter by role
curl "http://localhost:5000/api/jobs?role=analyst"

# Filter by location
curl "http://localhost:5000/api/jobs?location=Toronto"

# Limit results
curl "http://localhost:5000/api/jobs?limit=10"
```

## Development

### Add Custom Scraper

```python
# In browser_scraper.py

def scrape_custom_source():
    """Scrape from your custom source"""
    jobs = []
    try:
        # Your scraping code
        for job in custom_api_response:
            jobs.append({
                "title": job["job_title"],
                "company": job["employer"],
                "location": "Ontario, Canada",
                "url": job["link"],
                "posted_date": datetime.now().isoformat(),
                "is_student_job": 0,
                "source": "Custom Source"
            })
    except Exception as e:
        print(f"Custom Source error: {e}")
    return jobs

# Add to scrape_all_browser_jobs():
custom_jobs = scrape_custom_source()
all_jobs.extend(custom_jobs)
```

### Debug Scraper

```python
import logging

# Enable debug logging
logging.basicConfig(level=logging.DEBUG)

# Test with verbose output
from browser_scraper import scrape_all_browser_jobs
jobs = scrape_all_browser_jobs()

# Get statistics
from browser_scraper import get_scraper_stats
stats = get_scraper_stats()
print(stats)
```

## Monitoring

### Check Scraper Health

```python
from browser_scraper import get_scraper_stats

stats = get_scraper_stats()
print(f"Jobs found: {stats['total_jobs']}")
print(f"Duration: {stats['duration_seconds']}s")
print(f"Success rate: {stats['sources_succeeded']} sources")
print(f"Errors: {stats['sources_failed']} sources")
```

### Monitor Database

```bash
# Using SQLite CLI
sqlite3 jobs.db

# Count jobs by source
SELECT source, COUNT(*) FROM jobs GROUP BY source;

# Count by date
SELECT DATE(created_at), COUNT(*) FROM jobs GROUP BY DATE(created_at);
```

## Best Practices

### ✅ Do's

- ✓ Respect website terms of service
- ✓ Add delays between requests
- ✓ Use caching when possible
- ✓ Check robots.txt before scraping
- ✓ Handle errors gracefully
- ✓ Log problems for debugging
- ✓ Document custom scrapers

### ❌ Don'ts

- ✗ Scrape continuously without delays
- ✗ Ignore rate limit responses
- ✗ Scrape personal/private data
- ✗ Bypass authentication
- ✗ Store credentials in code
- ✗ Ignore website's robots.txt

## Support

### Getting Help

1. Check [SCRAPER_GUIDE.md](SCRAPER_GUIDE.md) for detailed docs
2. Run test suite: `python test_scraper_suite.py`
3. Check logs for errors
4. Review configuration in `scraper_config.py`

### Reporting Issues

Include:
- Error message/traceback
- Steps to reproduce
- Operating system
- Python version
- Recent configuration changes

## Updates

The scraper system is regularly updated with:
- New data sources
- Better error handling
- Performance improvements
- Additional filtering options

To update:
```bash
pip install -r requirements.txt --upgrade
```

---

**Last Updated**: 2024  
**Version**: 1.0  
**Status**: Production Ready ✓
