# Job Scraper Integration Guide

## Overview

The "Let the Jobs Find Me" application includes a sophisticated job scraping system that fetches job listings from multiple sources. The system is designed to be resilient and adaptive, automatically falling back to alternative methods when APIs are unavailable.

## Architecture

### Components

1. **browser_scraper.py** - Main scraping module with multiple strategies
2. **job_scraper.py** - Alternative scraper with Jooble and RemoteOK APIs
3. **scraper_simple.py** - Lightweight fallback scraper

### Scraping Strategy

The system uses a **tiered scraping approach**:

```
1. Try Fast APIs First
   ├─ Indeed API (scrape_indeed_api)
   ├─ LinkedIn Scraper (scrape_linkedin_api)
   └─ Glassdoor Scraper (scrape_glassdoor_api)

2. If APIs Fail → Use Browser Automation
   └─ Brave Browser with Selenium (scrape_with_brave_browser)

3. If Browser Fails → Use Sample Data
   └─ Demo jobs from sample database
```

## Features

### ✨ Brave Browser Integration

The system includes native support for Brave browser automation:

- **Automatic Detection**: Checks for Brave installation on Windows, macOS, and Linux
- **Selenium Integration**: Uses webdriver-manager for automatic driver management
- **Anti-Detection**: Includes user-agent spoofing and automation detection evasion
- **Graceful Fallback**: Automatically reverts to sample data if browser isn't available

### 🎯 Filtering & Keywords

Jobs are filtered by:

- **Keywords**: UI, UX, Designer, Research, Analyst, Data Analyst, Business Analyst, Product Manager
- **Location**: Ontario-based roles (Toronto, Ottawa, Kitchener, Waterloo, etc.)
- **Experience Level**: Option to filter for entry-level/internship positions

### 🔄 Duplicate Detection

The system automatically removes duplicate job listings using:
- Job title (normalized, lowercase)
- Job URL

## Installation

### 1. Install Base Requirements

```bash
pip install -r requirements.txt
```

### 2. Optional: Install Browser Automation Components

For Brave browser scraping:

```bash
pip install selenium webdriver-manager
```

### 3. Optional: Install Brave Browser

**Windows:**
```
Download from: https://brave.com/download/
or use: choco install brave (if using Chocolatey)
```

**macOS:**
```bash
brew install brave-browser
```

**Linux:**
```bash
sudo apt install brave-browser  # Ubuntu/Debian
# or
yay -S brave-browser            # Arch
```

## Usage

### Via Web Interface

1. Navigate to the "Scrape Jobs" section
2. Click **"Fetch Jobs"** button
3. Wait for the scraper to run (progress shown in browser console)
4. Jobs will appear in the main job list

### Via Python CLI

```python
from browser_scraper import scrape_all_browser_jobs

# Fetch all jobs
jobs = scrape_all_browser_jobs()

print(f"Found {len(jobs)} jobs")
for job in jobs[:5]:
    print(f"- {job['title']} @ {job['company']}")
```

### Via Flask API

```bash
curl -X POST http://localhost:5000/api/scrape-jobs
```

## Customization

### Add Custom Keywords

Edit `browser_scraper.py`:

```python
# In scrape_indeed_api(), scrape_linkedin_api(), etc.
keywords = ['UX Designer', 'Product Manager', 'YOUR_KEYWORD']
```

### Add New Data Sources

Create a new scraper function:

```python
def scrape_custom_source():
    """Fetch jobs from your custom source"""
    jobs = []
    
    try:
        # Your scraping logic here
        pass
    except Exception as e:
        print(f"Custom Source error: {str(e)}")
    
    return jobs

# Add to scrape_all_browser_jobs():
custom_jobs = scrape_custom_source()
all_jobs.extend(custom_jobs)
```

### Modify Sample Data

Edit `get_sample_jobs_for_demo()`:

```python
def get_sample_jobs_for_demo():
    """Fallback sample jobs"""
    return [
        {
            "title": "Your Job Title",
            "company": "Your Company",
            "location": "Toronto, ON",
            "role": "Your Role",
            "description": "Job description",
            "url": "https://your-url.com",
            "posted_date": datetime.now().isoformat(),
            "is_student_job": 1,
            "source": "Sample Data"
        },
        # Add more jobs...
    ]
```

## Troubleshooting

### Issue: "No jobs found"

**Solution 1**: Check internet connection
```bash
ping google.com
```

**Solution 2**: Verify APIs are accessible
```python
import requests
response = requests.get("https://ca.indeed.com", timeout=10)
print(response.status_code)
```

**Solution 3**: Check browser is installed
```bash
# Windows
where brave.exe

# macOS
which brave

# Linux
which brave-browser
```

### Issue: Brave browser not found

**Solution**:
1. Install Brave browser from https://brave.com/download/
2. Verify installation path:
   - Windows: `C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe`
   - macOS: `/Applications/Brave Browser.app/Contents/MacOS/Brave Browser`
   - Linux: `/usr/bin/brave-browser`

### Issue: "Selenium not installed"

**Solution**:
```bash
pip install selenium webdriver-manager
```

### Issue: Browser automation blocked by website

**Solution**:
The system has anti-detection measures, but some websites may still block Selenium. Try:

1. Use VPN/Proxy
2. Wait 5-10 minutes before retrying
3. Check website's `robots.txt`: `https://example.com/robots.txt`

### Issue: Timeout errors

**Solution**:
1. Increase timeout in `browser_scraper.py`:
   ```python
   response = requests.get(url, timeout=30)  # Increase from 10 to 30
   ```

2. Check your internet speed:
   ```bash
   speedtest-cli  # pip install speedtest-cli
   ```

## Performance Tips

### Speed Optimization

1. **Use API-based scrapers first** (faster than browser automation)
2. **Set realistic timeouts**: Too short = errors, too long = slow
3. **Limit results per query**: Extract only first 20-30 jobs per source
4. **Use caching**: Store jobs for 24 hours to avoid re-scraping

### Resource Usage

1. **Memory**: Browser automation uses ~500MB per instance
2. **CPU**: Concurrent scraping uses significant CPU
3. **Network**: Parallel requests may hit rate limits

## Rate Limiting & Ethics

### Best Practices

1. **Respect robots.txt**: Check `website.com/robots.txt`
2. **Add delays**: Use `time.sleep(1-2)` between requests
3. **Rotate User-Agents**: Use different browsers/devices
4. **Cache results**: Don't re-scrape the same data
5. **Contact websites**: Ask permission for scraping

### Common Rate Limits

- Indeed: ~2 requests/second
- LinkedIn: ~1 request/second  
- GitHub: 60 requests/hour (unauthenticated)
- Jooble: 10 requests/minute

## Database Integration

Jobs scraped are automatically saved to `jobs.db`:

```sql
SELECT * FROM jobs WHERE source = 'Indeed (Brave Browser)' LIMIT 10;
SELECT COUNT(*) FROM jobs WHERE is_student_job = 1;
```

## Advanced Configuration

### Environment Variables

Create `.env` file:

```
SCRAPER_TIMEOUT=15
SCRAPER_MAX_RESULTS=100
BRAVE_PATH=/custom/path/to/brave
DEBUG_SCRAPER=1
```

### Logging

Enable detailed logging:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Debugging

### Enable Verbose Output

```python
# In browser_scraper.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Check Scraper Status

```python
if __name__ == "__main__":
    import time
    start = time.time()
    jobs = scrape_all_browser_jobs()
    elapsed = time.time() - start
    
    print(f"Jobs found: {len(jobs)}")
    print(f"Time elapsed: {elapsed:.2f}s")
    print(f"Jobs per second: {len(jobs)/elapsed:.2f}")
```

### Monitor Browser Processes

**Windows (PowerShell)**:
```powershell
Get-Process brave | Measure-Object
```

**macOS/Linux**:
```bash
ps aux | grep brave | wc -l
```

## API Endpoints

### Scrape Jobs (POST)

```
POST /api/scrape-jobs
```

**Response**:
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

```
GET /api/jobs
GET /api/jobs?role=analyst&location=Toronto
```

## Contributing

To add new scrapers:

1. Create new function in `browser_scraper.py`
2. Follow the job object structure
3. Add error handling
4. Test with sample data
5. Update this guide

## Resources

- [Brave Browser](https://brave.com)
- [Selenium Documentation](https://selenium.dev)
- [Indeed API](https://opensource.indeedeng.io)
- [Beautiful Soup](https://www.crummy.com/software/BeautifulSoup/)
- [Requests Library](https://requests.readthedocs.io/)

## License

This scraper is provided as-is for educational and personal use. Respect website terms of service and robots.txt when scraping.

---

**Last Updated**: 2024  
**Version**: 1.0  
**Status**: Production Ready ✓
