# Job Scraper - Deployment Checklist

## Pre-Launch Verification

### Code Review
- [ ] browser_scraper.py reviewed for errors
- [ ] Error handling adequate
- [ ] No hardcoded secrets/credentials
- [ ] All imports present in requirements.txt
- [ ] Logging statements helpful but not excessive

### Testing
- [ ] Run quick test: `python test_scraper_suite.py --quick`
- [ ] Run full test suite: `python test_scraper_suite.py`
- [ ] Manual test with web UI
- [ ] Test all fallback scenarios
- [ ] Test with and without internet
- [ ] Test database operations
- [ ] Verify no errors in console

### Configuration
- [ ] Review scraper_config.py settings
- [ ] Verify keywords match your job market
- [ ] Confirm location filters are correct
- [ ] Check timeout values are reasonable
- [ ] Validate API keys (if using any)

### Dependencies
- [ ] All packages in requirements.txt
- [ ] selenium and webdriver-manager included
- [ ] Optional packages listed as optional
- [ ] No deprecated packages
- [ ] Python 3.7+ requirement noted

### Documentation Review
- [ ] SCRAPER_GUIDE.md exists and complete
- [ ] SCRAPER_USAGE.md exists and complete
- [ ] SCRAPER_CHEAT_SHEET.md exists and complete
- [ ] Inline code comments present
- [ ] README updated with scraper info (if applicable)

### Setup Automation
- [ ] setup_scraper.py works on target OS
- [ ] All checks pass for Python version
- [ ] Brave browser detection works
- [ ] Directory creation works
- [ ] Help text is clear

### Database
- [ ] jobs.db exists or creates on first run
- [ ] Schema matches application requirements
- [ ] Database can be backed up easily
- [ ] Query examples documented
- [ ] Cleanup/archival strategy in place (optional)

## Deployment Steps

### 1. System Preparation
```bash
# Clone or download project
cd "let the jobs find me"

# Create virtual environment (recommended)
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Environment Setup
```bash
# Install optional browser automation (recommended)
pip install selenium webdriver-manager

# (Optional) Install Brave browser
# https://brave.com/download/

# Create directories (if needed)
mkdir -p data logs cache backups
```

### 3. Verification
```bash
# Verify installation
python -c "import flask, requests, bs4; print('✓ Packages OK')"

# Test scraper
python test_scraper_suite.py --quick

# Test database
sqlite3 jobs.db ".tables"
```

### 4. Initial Configuration
```bash
# Review configuration
cat scraper_config.py

# Edit if needed (optional)
# nano scraper_config.py
# Adjust keywords, locations, timeouts

# Update .env (optional)
# Configure FLASK_ENV, DEBUG, etc.
```

### 5. Launch Application
```bash
# Development
python app.py

# Production (if using Gunicorn)
gunicorn app:app
```

### 6. First Run Test
- [ ] Web interface loads (http://localhost:5000)
- [ ] Click "Fetch Jobs"
- [ ] Wait for scraping to complete
- [ ] Jobs appear in list
- [ ] Database has new records
- [ ] No errors in console

## Production Deployment

### Hosting Options

#### Option 1: Local Machine
```bash
# Install requirements above
# Run app.py

# OR with auto-restart (using PM2)
pm2 start app.py --name "job-scraper"
```

#### Option 2: Docker
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

# Install Brave (optional)
RUN apt-get update && apt-get install -y brave-browser

COPY . .
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000"]
```

#### Option 3: Cloud Platform
- Heroku: `git push heroku main`
- DigitalOcean: App Platform
- AWS: Elastic Beanstalk
- Google Cloud: App Engine
- Azure: App Service

### Server Configuration

#### Required Components
- [ ] Python 3.7+
- [ ] All dependencies installed
- [ ] Brave browser (optional)
- [ ] SQLite or PostgreSQL
- [ ] Web server (Gunicorn, Uvicorn, etc.)

#### Security Checklist
- [ ] HTTPS enabled
- [ ] CORS configured properly
- [ ] No debug mode in production
- [ ] SECRET_KEY configured
- [ ] Rate limiting enabled
- [ ] Input validation active
- [ ] Logs secured

#### Performance Optimization
- [ ] Caching enabled (1 hour default)
- [ ] Database indexed
- [ ] Web server optimized (workers, threads)
- [ ] Separate job scraper tasks (optional)
- [ ] CDN for static files (optional)

### Monitoring & Maintenance

#### Monitoring
```bash
# Check application status
ps aux | grep app.py

# Monitor logs
tail -f app.log

# Check database
sqlite3 jobs.db "SELECT COUNT(*) FROM jobs;"

# Monitor resource usage
top  # or 'Get-Process' on Windows
```

#### Regular Maintenance
- [ ] Weekly: Check logs for errors
- [ ] Weekly: Verify scraper is running
- [ ] Weekly: Check database size
- [ ] Monthly: Review job data quality
- [ ] Monthly: Update scraper if needed
- [ ] Quarterly: Update dependencies

#### Backup Strategy
```bash
# Daily backup
cp jobs.db backups/jobs_$(date +%Y%m%d).db

# Weekly full backup
tar czf backups/full_$(date +%Y%m%d).tar.gz .

# Archive old jobs (optional)
# sqlite3 jobs.db "INSERT INTO jobs_archive SELECT * FROM jobs WHERE created_at < date('now', '-90 days');"
```

## Troubleshooting Deployment

### Application Won't Start
```bash
# Check Python version
python --version

# Check dependencies
pip list

# Check database
sqlite3 jobs.db ".tables"

# Check logs
grep -i error app.log
```

### Scraper Not Working
```bash
# Test manually
python -c "from browser_scraper import scrape_all_browser_jobs; print(len(scrape_all_browser_jobs()))"

# Check internet
ping google.com

# Check Brave (if installed)
which brave-browser
```

### Performance Issues
- Increase timeout settings
- Enable caching
- Reduce jobs per source
- Check database size
- Monitor CPU/RAM usage

### Database Issues
```bash
# Check integrity
sqlite3 jobs.db "PRAGMA integrity_check;"

# Optimize database
sqlite3 jobs.db "VACUUM;"

# Rebuild indexes
sqlite3 jobs.db "REINDEX;"
```

## Post-Launch Verification

- [ ] Application accessible via URL
- [ ] "Fetch Jobs" works without errors
- [ ] Jobs persist after scraping
- [ ] Database can be queried
- [ ] No console errors
- [ ] Logs containing expected messages
- [ ] Performance acceptable
- [ ] Mobile view works (if applicable)

## Rollback Plan

If deployment fails:

```bash
# Stop application
pkill -f "python app.py"

# Restore previous version (git)
git revert HEAD

# Restore database backup (if corrupted)
cp backups/jobs_latest.db jobs.db

# Restart
python app.py
```

## Documentation for Users

Provide users with:
- [ ] Quick start guide (copy SCRAPER_USAGE.md)
- [ ] Cheat sheet (copy SCRAPER_CHEAT_SHEET.md)
- [ ] Support contact info
- [ ] Issue reporting format
- [ ] Feature request process

## Sign-Off

Production Launch Sign-Off:

- [ ] All tests passing
- [ ] Code reviewed
- [ ] Documentation complete
- [ ] Deployment verified
- [ ] Monitoring in place
- [ ] Backup strategy confirmed
- [ ] Team trained
- [ ] Go-live approval obtained

**Deployment Date**: _______________

**Deployed By**: _______________

**Approved By**: _______________

---

## Useful Commands Reference

### Development
```bash
# Start dev server
python app.py

# Run tests
python test_scraper_suite.py

# Setup scraper
python setup_scraper.py
```

### Database
```bash
# Connect
sqlite3 jobs.db

# Check size
ls -lh jobs.db

# Backup
cp jobs.db jobs_backup.db

# Export
sqlite3 jobs.db ".mode csv" ".output jobs.csv" "SELECT * FROM jobs;"
```

### Monitoring
```bash
# Check process
ps aux | grep python

# View logs
tail -100 app.log

# Monitor live
watch -n 1 'ps aux | grep app'
```

## Quick Deployment (5 minutes)

```bash
# 1. Setup
python setup_scraper.py

# 2. Test
python test_scraper_suite.py --quick

# 3. Run
python app.py

# 4. Open
# http://localhost:5000

# 5. Use
# Click "Fetch Jobs"
```

---

**Last Updated**: 2024  
**Version**: 1.0  
**Status**: Ready for Production ✓
