#!/usr/bin/env python3
"""
Remove all example jobs from the database
"""
import sqlite3

DB_PATH = 'jobs.db'

def clear_all_jobs():
    """Remove all jobs from database"""
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        
        # Get initial count
        c.execute('SELECT COUNT(*) as count FROM jobs')
        initial_count = c.fetchone()['count']
        
        # Delete all jobs
        c.execute('DELETE FROM jobs')
        c.execute('DELETE FROM applications')
        c.execute('DELETE FROM bookmarks')
        
        conn.commit()
        
        # Get final count
        c.execute('SELECT COUNT(*) as count FROM jobs')
        final_count = c.fetchone()['count']
        
        conn.close()
        
        print("=" * 60)
        print("DATABASE CLEARED")
        print("=" * 60)
        print(f"Jobs removed: {initial_count}")
        print(f"Jobs remaining: {final_count}")
        print("=" * 60)
        print("\n✓ All example jobs have been removed")
        print("✓ Database is now empty and ready for real jobs")
        print("✓ Use 'Start Scraping' to import real jobs")
            
    except Exception as e:
        print(f"✗ Error clearing database: {str(e)}")

if __name__ == '__main__':
    clear_all_jobs()
