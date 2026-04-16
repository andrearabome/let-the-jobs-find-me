# Job Scraper Cheat Sheet

## Quick Commands

### Setup & Installation
```bash
# One-time setup
python setup_scraper.py

# Install dependencies
pip install -r requirements.txt

# Install optional browser automation
pip install selenium webdriver-manager
```

### Running the App
```bash
# Start Flask server
python app.py

# Access web interface
# http://localhost:5000

# Click "Fetch Jobs" to scrape
```

### Testing
```bash
# Quick test
python test_scraper_suite.py --quick

# Full test suite
python test_scraper_suite.py

# Test specific module
python -c "from browser_scraper import scrape_all_browser_jobs; jobs = scrape_all_browser_jobs(); print(f'Found {len(jobs)} jobs')"
```

## Database Queries

### SQLite Commands
```bash
# Connect to database
sqlite3 jobs.db

# Count total jobs
SELECT COUNT(*) FROM jobs;

# Get jobs by source
SELECT source, COUNT(*) FROM jobs GROUP BY source;

# Export to CSV
.mode csv
.output jobs_export.csv
SELECT * FROM jobs;

# View schema
.schema jobs
```

## Common Issues & Solutions

### Issue: "Module not found"
```bash
# Solution:
pip install -r requirements.txt
```

### Issue: "No jobs found"
```bash
# Check internet
python -c "import requests; print(requests.get('https://google.com', timeout=5).status_code)"

# Check Brave
python -c "import os; print(os.path.exists('C:\\\\Program Files\\\\BraveSoftware\\\\Brave-Browser\\\\Application\\\\brave.exe'))"

# Use sample data
python -c "from browser_scraper import get_sample_jobs_for_demo; print(len(get_sample_jobs_for_demo()))"
```

### Issue: "Selenium not found"
```bash
# Solution:
pip install selenium webdriver-manager
```

### Issue: "Timeout errors"
```python
# Edit browser_scraper.py and increase timeout:
response = requests.get(url, timeout=30)  # was 15
```

## Configuration Files

### scraper_config.py
- Keywords to search
- Locations to filter
- Timeouts
- API settings
- Browser options

### .env (create if needed)
```
FLASK_ENV=development
FLASK_DEBUG=False
```

### requirements.txt
- Flask dependencies
- Selenium dependencies
- Request libraries

## File Structure

```
project/
├── app.py                      # Flask web app
├── browser_scraper.py          # Main scraper
├── job_scraper.py             # Alternative scraper
├── scraper_config.py          # Configuration
├── setup_scraper.py           # Setup script
├── test_scraper_suite.py      # Tests
├── jobs.db                    # SQLite database
├── requirements.txt           # Python packages
├── SCRAPER_GUIDE.md          # Detailed guide
├── SCRAPER_USAGE.md          # Usage guide
├── templates/                 # HTML templates
├── static/                    # CSS/JS
├── backend/                   # Backend code
└── frontend/                  # Frontend code
```

## Performance Metrics

| Task | Time | Status |
|------|------|--------|
| API scraping | 10-30s | ✓ Fast |
| Browser scraping | 30-60s | ✓ Moderate |
| Sample data load | <1s | ✓ Instant |
| Database insert | 1-5s | ✓ Fast |
| Total scrape | 30-65s | ✓ Good |

## Python One-Liners

```python
# Get all jobs
python -c "from browser_scraper import scrape_all_browser_jobs; print(len(scrape_all_browser_jobs()))"

# Get sample jobs
python -c "from browser_scraper import get_sample_jobs_for_demo; jobs = get_sample_jobs_for_demo(); print([j['title'] for j in jobs])"

# Get scraper statistics
python -c "from browser_scraper import get_scraper_stats; import json; print(json.dumps(get_scraper_stats(), indent=2))"

# Validate job format
python -c "from browser_scraper import get_sample_jobs_for_demo; jobs = get_sample_jobs_for_demo(); print('All fields present' if all('title' in j and 'company' in j for j in jobs) else 'Missing fields')"

# Count unique companies
python -c "from browser_scraper import scrape_all_browser_jobs; jobs = scrape_all_browser_jobs(); companies = set(j['company'] for j in jobs); print(f'Unique companies: {len(companies)}')"
```

## Browser Paths

### Windows
```
C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe
C:\Program Files (x86)\BraveSoftware\Brave-Browser\Application\brave.exe
```

### macOS
```
/Applications/Brave Browser.app/Contents/MacOS/Brave Browser
```

### Linux
```
/usr/bin/brave-browser
/snap/bin/brave
```

## Environment Setup

### Windows PowerShell
```powershell
# Create virtual environment
python -m venv venv

# Activate
venv\Scripts\Activate.ps1

# Install packages
pip install -r requirements.txt

# Run app
python app.py
```

### macOS/Linux
```bash
# Create virtual environment
python3 -m venv venv

# Activate
source venv/bin/activate

# Install packages
pip install -r requirements.txt

# Run app
python3 app.py
```

## API Endpoints

### POST /api/scrape-jobs
Start job scraping
```bash
curl -X POST http://localhost:5000/api/scrape-jobs
```

### GET /api/jobs
Get all jobs (with optional filters)
```bash
curl http://localhost:5000/api/jobs
curl "http://localhost:5000/api/jobs?role=analyst"
curl "http://localhost:5000/api/jobs?location=Toronto"
```

## Logging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Log Files
```bash
# View recent logs
tail -f scraper.log

# Search logs
grep -i "error" scraper.log
grep -i "indeed" scraper.log
```

## Tips & Tricks

### 💡 Tip 1: Cache Results
Avoid re-scraping by caching jobs:
```python
ENABLE_CACHE = True
CACHE_DURATION = 3600  # 1 hour
```

### 💡 Tip 2: Use Sample Data for Testing
Testing browser components:
```python
from browser_scraper import get_sample_jobs_for_demo
jobs = get_sample_jobs_for_demo()  # No API calls needed
```

### 💡 Tip 3: Monitor Scraper Health
Check statistics:
```python
from browser_scraper import get_scraper_stats
stats = get_scraper_stats()
print(f"Performance: {stats['duration_seconds']}s")
```

### 💡 Tip 4: Rate Limiting
Add delays to be respectful:
```python
DELAY_BETWEEN_REQUESTS = 1
```

### 💡 Tip 5: Browser Automation
Use Brave for advanced scraping:
```python
from browser_scraper import scrape_with_brave_browser
jobs = scrape_with_brave_browser()
```

## Debugging Checklist

- [ ] Check internet connection
- [ ] Verify Python version (3.7+)
- [ ] Confirm dependencies installed
- [ ] Check Brave browser installed (optional)
- [ ] Verify database exists
- [ ] Review error logs
- [ ] Test with sample data
- [ ] Check API accessibility
- [ ] Increase timeout if slow
- [ ] Try clearing cache

## Resources

- [Brave Browser](https://brave.com)
- [Selenium Docs](https://selenium.dev)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- [Requests Library](https://requests.readthedocs.io/)
- [Python SQLite](https://docs.python.org/3/library/sqlite3.html)

## Version Info

```python
# Check versions
python --version
pip list | grep -E "flask|requests|selenium"

# Python code:
import requests
import flask
print(f"Flask: {flask.__version__}")
print(f"Requests: {requests.__version__}")
```

## File Quick Reference

| File | Purpose |
|------|---------|
| `app.py` | Flask web server |
| `browser_scraper.py` | Main scraper logic |
| `job_scraper.py` | Alternative scraper |
| `scraper_config.py` | Configuration |
| `setup_scraper.py` | Setup automation |
| `test_scraper_suite.py` | Test suite |
| `jobs.db` | SQLite database |
| `SCRAPER_GUIDE.md` | Full documentation |
| `SCRAPER_USAGE.md` | Usage guide |

## Quick Troubleshooting Tree

```
No jobs found?
├─ Check internet → ping google.com
├─ Check APIs → curl https://ca.indeed.com
├─ Check Brave → Locate Brave executable
└─ Use sample → python -c "from browser_scraper import get_sample_jobs_for_demo"

Module errors?
├─ Missing imports → pip install -r requirements.txt
├─ Virtual env? → Activate venv
└─ Python 3.7+? → python --version

Slow scraping?
├─ Increase timeout → TIMEOUT = 30
├─ Reduce results → MAX_JOBS = 10
└─ Use caching → ENABLE_CACHE = True

Browser issues?
├─ Install Brave → https://brave.com/download/
├─ Install Selenium → pip install selenium webdriver-manager
└─ Check path → python -c "import os; print(os.path.exists(...))"
```

---

**Last Updated**: 2024  
**Quick Reference Version**: 1.0  
**Status**: Ready to Use ✓
