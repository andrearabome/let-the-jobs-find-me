from flask import Flask, render_template, request, jsonify, send_file, make_response
from flask_cors import CORS
import sqlite3
import json
from datetime import datetime
import os
import requests
import time
import re
from urllib.parse import urlsplit, urlunsplit, parse_qsl, urlencode
from browser_scraper import (
    scrape_all_browser_jobs,
    scrape_indeed_api,
    scrape_indeed_via_search_index,
    scrape_with_brave_browser,
    scrape_board_via_search_index,
    scrape_jobbank,
)

try:
    from flask_compress import Compress
except ImportError:
    Compress = None

app = Flask(__name__)
CORS(app)
app.config['COMPRESS_MIMETYPES'] = [
    'text/html',
    'text/css',
    'application/json',
    'application/javascript',
    'text/javascript'
]
app.config['COMPRESS_LEVEL'] = 6
app.config['COMPRESS_MIN_SIZE'] = 500
if Compress is not None:
    Compress(app)

# Database setup
DB_PATH = 'jobs.db'

# Lightweight in-memory cache for fast job list refreshes
JOBS_CACHE = {}
JOBS_CACHE_TTL_SECONDS = 20
TARGET_CITIES = ['Ottawa', 'Kitchener', 'Waterloo', 'Guelph', 'Mississauga', 'Toronto']
ALLOWED_CITIES = set(TARGET_CITIES)

def _jobs_cache_key(role, location, search, student_only, page):
    return (role, location, search, student_only, page)

def _get_jobs_cache(key):
    entry = JOBS_CACHE.get(key)
    if not entry:
        return None

    if time.time() - entry['timestamp'] > JOBS_CACHE_TTL_SECONDS:
        JOBS_CACHE.pop(key, None)
        return None

    return entry['payload']

def _set_jobs_cache(key, payload):
    JOBS_CACHE[key] = {
        'timestamp': time.time(),
        'payload': payload
    }

def invalidate_jobs_cache():
    JOBS_CACHE.clear()


def clear_non_bookmarked_jobs():
    """Delete all non-bookmarked jobs and their applications before a fresh scrape."""
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute('''
            SELECT id FROM jobs
            WHERE id NOT IN (SELECT job_id FROM bookmarks)
        ''')
        rows = c.fetchall()
        job_ids = [row['id'] for row in rows]

        if not job_ids:
            conn.close()
            return 0

        placeholders = ','.join('?' * len(job_ids))

        c.execute(f'DELETE FROM applications WHERE job_id IN ({placeholders})', job_ids)
        c.execute(f'DELETE FROM jobs WHERE id IN ({placeholders})', job_ids)

        conn.commit()
        conn.close()
        return len(job_ids)
    except Exception as e:
        print(f"[✗] Error clearing non-bookmarked jobs: {str(e)}")
        return 0


@app.route('/api/jobs/clear-non-bookmarked', methods=['POST'])
def clear_non_bookmarked_jobs_route():
    """Clear all non-bookmarked jobs so the next scrape starts from bookmarks only."""
    removed_jobs = clear_non_bookmarked_jobs()
    invalidate_jobs_cache()
    return jsonify({'success': True, 'removed_jobs': removed_jobs}), 200

def init_db():
    """Initialize database with tables"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            company TEXT NOT NULL,
            location TEXT NOT NULL,
            role TEXT NOT NULL,
            description TEXT,
            url TEXT,
            posted_date TEXT,
            salary TEXT,
            is_student_job INTEGER DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Add is_student_job column if it doesn't exist (for existing databases)
    try:
        c.execute('ALTER TABLE jobs ADD COLUMN is_student_job INTEGER DEFAULT 0')
    except sqlite3.OperationalError:
        pass  # Column already exists
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL,
            status TEXT DEFAULT 'interested',
            notes TEXT,
            applied_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    ''')
    
    c.execute('''
        CREATE TABLE IF NOT EXISTS bookmarks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_id INTEGER NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (job_id) REFERENCES jobs(id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS seen_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_key TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS deleted_jobs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            job_key TEXT NOT NULL UNIQUE,
            title TEXT,
            company TEXT,
            url TEXT,
            deleted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')

    # Indexes for fast refresh/filtering
    c.execute('CREATE INDEX IF NOT EXISTS idx_jobs_created_at ON jobs(created_at DESC)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_jobs_role ON jobs(role)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_jobs_student ON jobs(is_student_job)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_jobs_title_company ON jobs(title, company)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_seen_jobs_key ON seen_jobs(job_key)')
    c.execute('CREATE INDEX IF NOT EXISTS idx_deleted_jobs_key ON deleted_jobs(job_key)')
    
    conn.commit()
    conn.close()

def get_db():
    """Get database connection"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def normalize_location(raw_location, title='', description=''):
    """Normalize location text into consistent city labels used by filters."""
    combined = f"{raw_location} {title} {description}".lower()

    city_keywords = {
        'Ottawa': ['ottawa'],
        'Kitchener': ['kitchener'],
        'Waterloo': ['waterloo'],
        'Guelph': ['guelph'],
        'Mississauga': ['mississauga'],
        'Toronto': ['toronto', 'greater toronto area', 'gta']
    }

    for city, keywords in city_keywords.items():
        if any(keyword in combined for keyword in keywords):
            return city

    if 'remote' in combined:
        return 'Remote'

    if raw_location:
        location_text = str(raw_location).strip()
        if ',' in location_text:
            location_text = location_text.split(',')[0].strip()

        # Province-only values are not specific enough for the location filter.
        province_only = {'ontario', 'on', 'ontario canada', 'ontario, canada'}
        if location_text.lower() in province_only:
            return 'Toronto'

        if location_text in ALLOWED_CITIES:
            return location_text

    # Guaranteed city fallback for scraped jobs when source is vague or outside allowed cities.
    return 'Toronto'


def normalize_existing_locations():
    """Backfill normalized location values for existing rows."""
    try:
        conn = get_db()
        c = conn.cursor()

        c.execute('SELECT id, location, title, description FROM jobs')
        jobs = c.fetchall()

        updates = 0
        for job in jobs:
            normalized = normalize_location(job['location'], job['title'], job['description'] or '')
            if normalized != job['location']:
                c.execute('UPDATE jobs SET location = ? WHERE id = ?', (normalized, job['id']))
                updates += 1

        if updates:
            conn.commit()
            print(f"[✓] Normalized locations for {updates} jobs")

        conn.close()
    except Exception as e:
        print(f"[✗] Error normalizing locations: {str(e)}")

def is_valid_job(job):
    """Validate that a job has all required fields and non-empty values"""
    required_fields = ['title', 'company', 'location', 'url']
    
    # Check all required fields exist and are not empty
    for field in required_fields:
        if field not in job or not job.get(field) or str(job.get(field)).strip() == '':
            return False
    
    # Check URL is valid format
    url = str(job.get('url', ''))
    if not url.startswith('http://') and not url.startswith('https://'):
        return False
    
    # Check title and company are not too short
    title = str(job.get('title', '')).strip()
    company = str(job.get('company', '')).strip()
    
    if len(title) < 3 or len(company) < 2:
        return False
    
    return True


def canonicalize_job_url(raw_url):
    """Normalize URLs so tracking params do not create duplicate rows."""
    url = str(raw_url or '').strip()
    if not url:
        return ''

    try:
        parts = urlsplit(url)
        filtered_query = []
        for key, value in parse_qsl(parts.query, keep_blank_values=True):
            key_lower = key.lower()
            if key_lower.startswith('utm_'):
                continue
            if key_lower in {'from', 'src', 'ref', 'trackid', 'trk', 'gh_jid'}:
                continue
            filtered_query.append((key, value))

        normalized_query = urlencode(sorted(filtered_query))
        normalized_path = parts.path.split(';', 1)[0]
        normalized_path = normalized_path.rstrip('/') if normalized_path != '/' else normalized_path
        return urlunsplit((parts.scheme.lower(), parts.netloc.lower(), normalized_path, normalized_query, ''))
    except Exception:
        return url.lower()


def _normalize_key_text(value):
    text = str(value or '').strip().lower()
    text = re.sub(r'\s+', ' ', text)
    text = re.sub(r'[^a-z0-9 ]+', '', text)
    return text


def build_job_key(title, company, url):
    """Create a stable duplicate key for one scrape run/import operation."""
    title_norm = _normalize_key_text(title)
    company_norm = _normalize_key_text(company)
    url_norm = canonicalize_job_url(url)
    return f"{title_norm}::{company_norm}::{url_norm}"


def should_block_deleted_rescrape():
    """Return True when deleted jobs should be blocked from future scrapes."""
    return os.getenv('BLOCK_DELETED_RESCRAPE', '1') == '1'

def clean_database():
    """Remove jobs with empty or invalid data"""
    try:
        conn = get_db()
        c = conn.cursor()
        
        # Get all jobs
        c.execute('SELECT id, title, company, location, url FROM jobs')
        jobs = c.fetchall()
        
        deleted_count = 0
        invalid_ids = []
        
        for job in jobs:
            # Check for empty/null fields
            fields_valid = all([job['title'], job['company'], job['location'], job['url']])
            
            if not fields_valid:
                invalid_ids.append(job['id'])
                deleted_count += 1
                continue
            
            # Check URL format
            url = str(job['url']).strip()
            if not (url.startswith('http://') or url.startswith('https://')):
                invalid_ids.append(job['id'])
                deleted_count += 1
        
        # Delete invalid jobs
        if invalid_ids:
            placeholders = ','.join('?' * len(invalid_ids))
            c.execute(f'DELETE FROM jobs WHERE id IN ({placeholders})', invalid_ids)
            conn.commit()
            print(f"[✓] Cleaned database: Removed {deleted_count} invalid job entries")
        
        conn.close()
    except Exception as e:
        print(f"[✗] Error cleaning database: {str(e)}")


@app.route('/')
def index():
    response = make_response(render_template('index.html', cache_bust=int(time.time())))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    """Get jobs with pagination (30 per page) and optional filters"""
    role = request.args.get('role', '')
    location = request.args.get('location', '')
    search = request.args.get('search', '')
    student_only = request.args.get('student', '').lower() == 'true'
    try:
        page = max(1, int(request.args.get('page', 1)))
    except ValueError:
        page = 1

    cache_key = _jobs_cache_key(role, location, search, student_only, page)
    cached_payload = _get_jobs_cache(cache_key)
    if cached_payload is not None:
        return jsonify(cached_payload)
    
    # Pagination settings
    jobs_per_page = 10
    offset = (page - 1) * jobs_per_page
    
    conn = get_db()
    c = conn.cursor()
    
    query = 'SELECT * FROM jobs WHERE 1=1'
    params = []
    
    if role:
        query += ' AND role = ?'
        params.append(role)
    
    if location:
        normalized_filter_location = normalize_location(location)
        query += ' AND location = ?'
        params.append(normalized_filter_location)
    
    if search:
        query += ' AND (title LIKE ? OR company LIKE ?)'
        params.append(f'%{search}%')
        params.append(f'%{search}%')
    
    if student_only:
        query += ' AND is_student_job = 1'

    # Fast deterministic ordering for quick refresh
    query += ' ORDER BY created_at DESC, id DESC'
    
    # Get total count first (before LIMIT/OFFSET)
    count_query = query.replace('SELECT *', 'SELECT COUNT(*) as count')
    c.execute(count_query, params)
    total_count = c.fetchone()['count']
    
    # Get page data with pagination
    query += f' LIMIT {jobs_per_page} OFFSET {offset}'
    c.execute(query, params)
    jobs = c.fetchall()
    conn.close()
    
    # Convert to list of dicts
    jobs_list = [dict(job) for job in jobs]
    
    # Add bookmark status for each job
    bookmark_conn = get_db()
    bookmark_c = bookmark_conn.cursor()
    for job in jobs_list:
        bookmark_c.execute('SELECT COUNT(*) as is_bookmarked FROM bookmarks WHERE job_id = ?', (job['id'],))
        bookmark_result = bookmark_c.fetchone()
        job['is_bookmarked'] = bookmark_result['is_bookmarked'] > 0
    bookmark_conn.close()
    
    # Filter out invalid jobs (empty fields, bad URLs)
    jobs_list = [job for job in jobs_list if is_valid_job(job)]
    
    # Calculate pagination info
    total_pages = (total_count + jobs_per_page - 1) // jobs_per_page
    
    payload = {
        'jobs': jobs_list,
        'pagination': {
            'current_page': page,
            'total_pages': total_pages,
            'total_jobs': total_count,
            'jobs_per_page': jobs_per_page,
            'has_next': page < total_pages,
            'has_prev': page > 1
        }
    }

    _set_jobs_cache(cache_key, payload)
    return jsonify(payload)

@app.route('/api/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get a single job with application and bookmark status"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('SELECT * FROM jobs WHERE id = ?', (job_id,))
    job = c.fetchone()
    
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    
    c.execute('SELECT * FROM applications WHERE job_id = ?', (job_id,))
    application = c.fetchone()
    
    c.execute('SELECT COUNT(*) as is_bookmarked FROM bookmarks WHERE job_id = ?', (job_id,))
    bookmark = c.fetchone()
    
    conn.close()
    
    job_dict = dict(job)
    job_dict['application'] = dict(application) if application else None
    job_dict['is_bookmarked'] = bookmark['is_bookmarked'] > 0
    
    return jsonify(job_dict)

@app.route('/api/jobs', methods=['POST'])
def add_job():
    """Add a new job"""
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        INSERT INTO jobs (title, company, location, role, description, url, salary, posted_date)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        data.get('title'),
        data.get('company'),
        normalize_location(data.get('location'), data.get('title', ''), data.get('description', '')),
        data.get('role'),
        data.get('description', ''),
        data.get('url', ''),
        data.get('salary', ''),
        datetime.now().isoformat()
    ))
    
    conn.commit()
    job_id = c.lastrowid
    conn.close()

    invalidate_jobs_cache()
    
    return jsonify({'id': job_id}), 201

@app.route('/api/jobs/<int:job_id>', methods=['PUT'])
def update_job(job_id):
    """Update a job"""
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        UPDATE jobs SET title = ?, company = ?, location = ?, role = ?, 
                       description = ?, url = ?, salary = ?, is_student_job = ?
        WHERE id = ?
    ''', (
        data.get('title'),
        data.get('company'),
        normalize_location(data.get('location'), data.get('title', ''), data.get('description', '')),
        data.get('role'),
        data.get('description', ''),
        data.get('url', ''),
        data.get('salary', ''),
        1 if data.get('is_student_job', False) else 0,
        job_id
    ))
    
    conn.commit()
    conn.close()

    invalidate_jobs_cache()
    
    return jsonify({'success': True})

@app.route('/api/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job and related data"""
    conn = get_db()
    c = conn.cursor()

    # Optional persistent blocklist: prevent deleted jobs from reappearing.
    c.execute('SELECT title, company, url FROM jobs WHERE id = ?', (job_id,))
    existing_job = c.fetchone()

    if existing_job and should_block_deleted_rescrape():
        deleted_key = build_job_key(existing_job['title'], existing_job['company'], existing_job['url'])
        c.execute(
            'INSERT OR IGNORE INTO deleted_jobs (job_key, title, company, url) VALUES (?, ?, ?, ?)',
            (deleted_key, existing_job['title'], existing_job['company'], existing_job['url'])
        )
    
    c.execute('DELETE FROM applications WHERE job_id = ?', (job_id,))
    c.execute('DELETE FROM bookmarks WHERE job_id = ?', (job_id,))
    c.execute('DELETE FROM jobs WHERE id = ?', (job_id,))
    
    conn.commit()
    conn.close()

    invalidate_jobs_cache()
    
    return jsonify({'success': True})

@app.route('/api/applications', methods=['POST'])
def track_application():
    """Track an application"""
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    c.execute('DELETE FROM applications WHERE job_id = ?', (data.get('job_id'),))
    
    c.execute('''
        INSERT INTO applications (job_id, status, notes, applied_date)
        VALUES (?, ?, ?, ?)
    ''', (
        data.get('job_id'),
        data.get('status', 'interested'),
        data.get('notes', ''),
        data.get('applied_date', '')
    ))
    
    conn.commit()
    app_id = c.lastrowid
    conn.close()
    
    return jsonify({'id': app_id}), 201

@app.route('/api/bookmarks', methods=['POST'])
def add_bookmark():
    """Bookmark a job"""
    data = request.json
    conn = get_db()
    c = conn.cursor()
    
    try:
        c.execute('INSERT INTO bookmarks (job_id) VALUES (?)', (data.get('job_id'),))
        conn.commit()
        conn.close()
        invalidate_jobs_cache()
        return jsonify({'success': True}), 201
    except sqlite3.IntegrityError:
        conn.close()
        return jsonify({'error': 'Already bookmarked'}), 409

@app.route('/api/bookmarks/<int:job_id>', methods=['DELETE'])
def remove_bookmark(job_id):
    """Remove bookmark"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('DELETE FROM bookmarks WHERE job_id = ?', (job_id,))
    conn.commit()
    conn.close()
    invalidate_jobs_cache()
    
    return jsonify({'success': True})

@app.route('/api/bookmarks', methods=['GET'])
def get_bookmarks():
    """Get all bookmarked jobs"""
    conn = get_db()
    c = conn.cursor()
    
    c.execute('''
        SELECT j.* FROM jobs j
        INNER JOIN bookmarks b ON j.id = b.job_id
        ORDER BY b.created_at DESC
    ''')
    jobs = c.fetchall()
    conn.close()
    
    return jsonify([dict(job) for job in jobs])

@app.route('/api/filters', methods=['GET'])
def get_filters():
    """Get available filter options"""
    return jsonify({
        'roles': ['UI/UX', 'Research', 'Analyst'],
        'locations': TARGET_CITIES
    })


def _apply_default_scrape_env():
    """Apply default scrape settings for source-specific actions."""
    os.environ["ENABLE_EXTRA_SOURCES"] = "0"
    os.environ["BROWSER_HEADLESS"] = "1"
    os.environ["SCRAPE_FAST_MODE"] = "1"
    os.environ["SCRAPE_PARALLEL_SOURCES"] = "1"
    os.environ["SCRAPE_REQUEST_TIMEOUT"] = "5"
    os.environ["SCRAPE_SOURCE_TIMEOUT"] = "20"
    os.environ["SCRAPE_SOURCE_JOB_TARGET"] = "60"
    os.environ["SCRAPE_TOTAL_TIMEOUT"] = "70"


def _import_scraped_jobs(jobs, removed_jobs):
    """Insert scraped jobs and build a standard API response payload."""
    if not jobs:
        return jsonify({
            'success': False,
            'imported': 0,
            'duplicates_skipped': 0,
            'blocked_deleted': 0,
            'total_found': 0,
            'warning': 'No jobs found. Try broadening role terms or re-running in a few minutes.'
        }), 200

    conn = get_db()
    c = conn.cursor()
    count = 0
    duplicates = 0
    blocked_deleted = 0
    cities_found = set()
    seen_this_run = set()
    imported_by_source = {}
    imported_by_city = {}

    deleted_keys = set()
    if should_block_deleted_rescrape():
        c.execute('SELECT job_key FROM deleted_jobs')
        deleted_keys = {row['job_key'] for row in c.fetchall() if row['job_key']}

    # Prevent re-importing jobs that already exist in the database or were seen in prior scrapes.
    existing_keys = set()
    c.execute('SELECT title, company, url FROM jobs')
    for row in c.fetchall():
        existing_keys.add(build_job_key(row['title'], row['company'], row['url']))

    c.execute('SELECT job_key FROM seen_jobs')
    existing_keys.update({row['job_key'] for row in c.fetchall() if row['job_key']})

    for job_data in jobs:
        try:
            if not is_valid_job(job_data):
                continue

            normalized_location = normalize_location(
                job_data.get('location', ''),
                job_data.get('title', ''),
                job_data.get('description', '')
            )

            if normalized_location not in ALLOWED_CITIES:
                continue

            cities_found.add(normalized_location)

            run_key = build_job_key(
                job_data.get('title', ''),
                job_data.get('company', ''),
                job_data.get('url', '')
            )

            if run_key in seen_this_run:
                duplicates += 1
                continue
            if run_key in existing_keys:
                duplicates += 1
                continue
            if run_key in deleted_keys:
                blocked_deleted += 1
                continue

            seen_this_run.add(run_key)

            c.execute('''
                INSERT INTO jobs (title, company, location, role, description, url, posted_date, is_student_job)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                job_data['title'],
                job_data['company'],
                normalized_location,
                job_data['role'],
                job_data.get('description', ''),
                job_data['url'],
                job_data['posted_date'],
                1 if job_data.get('is_student_job', False) else 0
            ))
            c.execute(
                'INSERT OR IGNORE INTO seen_jobs (job_key) VALUES (?)',
                (run_key,)
            )
            count += 1

            source_name = str(job_data.get('source', 'Unknown')).strip() or 'Unknown'
            imported_by_source[source_name] = imported_by_source.get(source_name, 0) + 1
            imported_by_city[normalized_location] = imported_by_city.get(normalized_location, 0) + 1
        except Exception:
            continue

    conn.commit()
    conn.close()
    invalidate_jobs_cache()

    missing_cities = [city for city in TARGET_CITIES if city not in cities_found]
    return jsonify({
        'success': True,
        'imported': count,
        'duplicates_skipped': duplicates,
        'blocked_deleted': blocked_deleted,
        'total_found': count + duplicates,
        'non_bookmarked_cleared': removed_jobs,
        'cities_found': sorted(list(cities_found)),
        'missing_cities': missing_cities,
        'imported_by_source': dict(sorted(imported_by_source.items(), key=lambda item: (-item[1], item[0]))),
        'imported_by_city': dict(sorted(imported_by_city.items(), key=lambda item: (-item[1], item[0])))
    }), 201


def _run_single_source_scrape(source_name):
    """Run source-specific scrape flow for Indeed or JobBank."""
    removed_jobs = clear_non_bookmarked_jobs()
    _apply_default_scrape_env()

    jobs = []
    if source_name == 'indeed':
        os.environ["ENABLE_BROWSER_FALLBACK"] = "1"
        jobs = scrape_indeed_api() or []
        if not jobs:
            jobs = scrape_indeed_via_search_index() or []
        if not jobs:
            jobs = scrape_with_brave_browser(target_cities=TARGET_CITIES) or []
    elif source_name == 'jobbank':
        os.environ["ENABLE_BROWSER_FALLBACK"] = "1"
        jobs = scrape_jobbank() or []
    else:
        os.environ["ENABLE_BROWSER_FALLBACK"] = "1"
        jobs = scrape_all_browser_jobs() or []

    return _import_scraped_jobs(jobs, removed_jobs)


@app.route('/api/scrape-jobs/indeed', methods=['POST'])
def scrape_jobs_indeed():
    """Scrape jobs from Indeed only."""
    try:
        print("Starting Indeed-only scrape...")
        return _run_single_source_scrape('indeed')
    except Exception as e:
        print(f"Indeed scraping error: {str(e)}")
        return jsonify({'error': f'Indeed scraping failed: {str(e)}'}), 500


@app.route('/api/scrape-jobs/jobbank', methods=['POST'])
def scrape_jobs_jobbank():
    """Scrape jobs from JobBank only."""
    try:
        print("Starting JobBank-only scrape...")
        return _run_single_source_scrape('jobbank')
    except Exception as e:
        print(f"JobBank scraping error: {str(e)}")
        return jsonify({'error': f'JobBank scraping failed: {str(e)}'}), 500


@app.route('/api/scrape-jobs', methods=['POST'])
def scrape_jobs():
    """Scrape student jobs from all enabled sources (Indeed + JobBank)."""
    try:
        print("Starting all-source scrape (Indeed + JobBank)...")
        return _run_single_source_scrape('all')
    
    except Exception as e:
        print(f"Scraping error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Scraping failed: {str(e)}'}), 500


if __name__ == '__main__':
    init_db()
    normalize_existing_locations()
    clean_database()  # Remove invalid job entries on startup
    app.run(debug=False, port=5001)
