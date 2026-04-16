#!/usr/bin/env python3
"""
Debug script to test job scraper without Flask
Run this to see detailed output from each scraper
"""

from job_scraper import scrape_all_jobs
import sys

if __name__ == '__main__':
    print("\n" + "=" * 70)
    print("JOB SCRAPER DEBUG TEST")
    print("=" * 70)
    print("\nThis will test each job scraper and show detailed output.")
    print("Please wait, this may take 1-2 minutes...\n")
    
    try:
        jobs = scrape_all_jobs()
        
        print("\n" + "=" * 70)
        print(f"RESULTS: Found {len(jobs)} total jobs")
        print("=" * 70)
        
        if jobs:
            print("\nAll jobs found:")
            for i, job in enumerate(jobs, 1):
                print(f"\n{i}. {job['title']}")
                print(f"   Company: {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   Role: {job['role']}")
                print(f"   URL: {job['url']}")
        else:
            print("\n❌ NO JOBS FOUND!")
            print("\nPossible reasons:")
            print("  1. Job websites may have updated their HTML structure")
            print("  2. Internet connection issue or website blocking scraper")
            print("  3. No matching keywords found on the pages")
            print("\nCheck the output above for error messages.")
        
        sys.exit(0 if jobs else 1)
        
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
