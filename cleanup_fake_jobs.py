#!/usr/bin/env python3
"""
Remove fake/test jobs and keep only real jobs from the database
"""
import sqlite3

DB_PATH = 'jobs.db'

# List of known fake/test company names to remove
FAKE_COMPANIES = [
    'Tech Startup',
    'Innovation Labs',
    'Finance Corp',
    'Digital Agency',
    'University Research',
    'Consulting Firm',
    'E-commerce Platform',
    'Market Research',
    'Tech Giants',
    'Startup Studio',
    'Think Tank',
    'Retail Chain',
    'Software Company',
    'Consulting',
    'Tech Company',
    'Design Studio',
    'University',
    'Finance',
    'Creative Agency',
    'Innovation Hub',
    'App Developer',
    'Education Tech',
    'Banking',
    'Fintech Startup',
    'Healthcare Tech',
    'Manufacturing',
    'SaaS Company',
    'Academic',
    'Logistics',
    'Web Agency',
    'Tech Research',
]

def clean_database():
    """Remove fake test jobs from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get initial count
        c.execute('SELECT COUNT(*) as count FROM jobs')
        initial_count = c.fetchone()['count']
        
        # Remove fake jobs
        deleted_count = 0
        for company in FAKE_COMPANIES:
            c.execute('DELETE FROM jobs WHERE company = ?', (company,))
            deleted_count += c.rowcount
        
        conn.commit()
        
        # Get final count
        c.execute('SELECT COUNT(*) as count FROM jobs')
        final_count = c.fetchone()['count']
        
        conn.close()
        
        print("=" * 60)
        print("DATABASE CLEANUP REPORT")
        print("=" * 60)
        print(f"Initial job count: {initial_count}")
        print(f"Fake jobs removed: {deleted_count}")
        print(f"Real jobs remaining: {final_count}")
        print("=" * 60)
        
        if deleted_count > 0:
            print(f"\n✓ Successfully removed {deleted_count} fake/test jobs")
            print(f"✓ {final_count} real jobs remain in the database")
        else:
            print("\n✓ No fake jobs found to remove")
            
    except Exception as e:
        print(f"✗ Error cleaning database: {str(e)}")

if __name__ == '__main__':
    clean_database()
