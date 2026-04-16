# Scraper Configuration
# Copy this file and modify as needed

# API Timeout Settings (seconds)
API_TIMEOUT = 15
BROWSER_TIMEOUT = 30

# Scraping Limits
MAX_JOBS_PER_SOURCE = 25
MAX_CONCURRENT_THREADS = 3

# Keywords to search for
SEARCH_KEYWORDS = [
    'UX', 'UI', 'Designer',
    'Research', 'Analyst', 'Data Analyst',
    'Business Analyst', 'Product Manager',
    'Product Designer', 'Entry Level'
]

# Locations to filter for
ONTARIO_LOCATIONS = [
    'Ontario', 'Toronto', 'Ottawa', 'Mississauga',
    'Kitchener', 'Waterloo', 'Guelph', 'Hamilton',
    'London', 'Peterborough', 'Kingston', 'Remote'
]

# Browser Settings
BROWSER_SETTINGS = {
    'headless': True,  # Run browser in headless mode (no GUI)
    'disable_images': True,  # Faster loading
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
    'window_size': '1920,1080',
}

# Retry Settings
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# Sources to enable/disable
ENABLE_SOURCES = {
    'indeed_api': True,
    'linkedin': True,
    'glassdoor': True,
    'brave_browser': True,
    'sample_data': True,  # Use as fallback
}

# Proxy Settings (optional)
USE_PROXY = False
PROXY_LIST = [
    # 'http://proxy1:8080',
    # 'http://proxy2:8080',
]

# Rate Limiting
DELAY_BETWEEN_REQUESTS = 1  # seconds
DELAY_BETWEEN_SOURCES = 2  # seconds

# Caching
ENABLE_CACHE = True
CACHE_DURATION = 3600  # seconds (1 hour)
CACHE_FILE = 'jobs_cache.json'

# Database
DATABASE_PATH = 'jobs.db'

# Logging
LOG_LEVEL = 'INFO'  # DEBUG, INFO, WARNING, ERROR
LOG_FILE = 'scraper.log'

# Email notifications (optional)
SEND_EMAIL_ON_COMPLETION = False
EMAIL_TO = 'your-email@example.com'
EMAIL_SUBJECT = 'Job Scraping Complete'

# Slack notifications (optional)
SEND_SLACK_ON_ERROR = False
SLACK_WEBHOOK_URL = 'https://hooks.slack.com/services/YOUR/WEBHOOK/URL'

# Custom Headers
CUSTOM_HEADERS = {
    'Accept-Language': 'en-US,en;q=0.9',
    'Accept-Encoding': 'gzip, deflate',
    'Connection': 'keep-alive',
}

# Job Filters
FILTERS = {
    'minimum_salary': 40000,  # Optional
    'experience_level': ['Entry Level', 'Junior', 'Internship'],
    'employment_type': ['Full-time', 'Internship', 'Co-op'],
    'posted_within_days': 30,
}

# Student Jobs Indicators
STUDENT_JOB_KEYWORDS = [
    'internship', 'co-op', 'entry', 'junior',
    'graduate', 'fresh', 'recent', 'campus'
]
