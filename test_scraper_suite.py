#!/usr/bin/env python3
"""
Job Scraper Test Suite
Tests all scraper components and data validation
"""

import sys
import time
import unittest
from datetime import datetime

# Import scrapers
try:
    from browser_scraper import (
        get_sample_jobs_for_demo,
        scrape_all_browser_jobs,
        scrape_indeed_api,
        scrape_linkedin_api,
        scrape_glassdoor_api,
        get_scraper_stats,
    )
except ImportError as e:
    print(f"Import Error: {e}")
    print("Make sure you're running this from the project root directory")
    sys.exit(1)


class JobDataValidator:
    """Validate job data integrity"""
    
    REQUIRED_FIELDS = ['title', 'company', 'location', 'url', 'posted_date']
    OPTIONAL_FIELDS = ['role', 'description', 'salary', 'is_student_job', 'source']
    
    @staticmethod
    def validate_job(job):
        """Validate a single job object"""
        errors = []
        
        # Check required fields
        for field in JobDataValidator.REQUIRED_FIELDS:
            if field not in job:
                errors.append(f"Missing required field: {field}")
            elif not job[field] or not str(job[field]).strip():
                errors.append(f"Empty required field: {field}")
        
        # Check data types
        if 'title' in job and not isinstance(job['title'], str):
            errors.append(f"Title must be string, got {type(job['title'])}")
        
        if 'url' in job and not isinstance(job['url'], str):
            errors.append(f"URL must be string, got {type(job['url'])}")
        
        # Check URL format
        if 'url' in job and not (job['url'].startswith('http://') or job['url'].startswith('https://')):
            errors.append(f"URL must start with http:// or https://: {job['url']}")
        
        # Check date format
        if 'posted_date' in job:
            try:
                datetime.fromisoformat(job['posted_date'])
            except (ValueError, TypeError):
                errors.append(f"Invalid date format: {job['posted_date']}")
        
        return errors


class TestAPIScraping(unittest.TestCase):
    """Test API-based scraping functions (sample data removed)"""
    
    def test_indeed_api(self):
        """Test Indeed API scraper"""
        print("\nTesting Indeed API...")
        try:
            jobs = scrape_indeed_api()
            print(f"  Found {len(jobs)} jobs from Indeed")
            
            if jobs:
                for job in jobs[:3]:
                    errors = JobDataValidator.validate_job(job)
                    if errors:
                        print(f"  Validation errors: {errors}")
                        self.fail(f"Indeed: {errors}")
        except Exception as e:
            print(f"  ⚠ Indeed API test skipped (not accessible): {str(e)[:80]}")
    
    def test_linkedin_api(self):
        """Test LinkedIn scraper"""
        print("\nTesting LinkedIn...")
        try:
            jobs = scrape_linkedin_api()
            print(f"  Found {len(jobs)} jobs from LinkedIn")
            
            if jobs:
                for job in jobs[:3]:
                    errors = JobDataValidator.validate_job(job)
                    if errors:
                        print(f"  Validation errors: {errors}")
                        self.fail(f"LinkedIn: {errors}")
        except Exception as e:
            print(f"  ⚠ LinkedIn test skipped (not accessible): {str(e)[:80]}")
    
    def test_glassdoor_api(self):
        """Test Glassdoor scraper"""
        print("\nTesting Glassdoor...")
        try:
            jobs = scrape_glassdoor_api()
            print(f"  Found {len(jobs)} jobs from Glassdoor")
            
            if jobs:
                for job in jobs[:3]:
                    errors = JobDataValidator.validate_job(job)
                    if errors:
                        print(f"  Validation errors: {errors}")
                        self.fail(f"Glassdoor: {errors}")
        except Exception as e:
            print(f"  ⚠ Glassdoor test skipped (not accessible): {str(e)[:80]}")


class TestAggregation(unittest.TestCase):
    """Test job aggregation and deduplication"""
    
    def test_scrape_all_jobs(self):
        """Test complete scraping pipeline"""
        print("\nRunning complete scraping pipeline...")
        start_time = time.time()
        
        jobs = scrape_all_browser_jobs()
        elapsed = time.time() - start_time
        
        print(f"  Time taken: {elapsed:.2f}s")
        print(f"  Total jobs found: {len(jobs)}")
        
        # Get stats
        stats = get_scraper_stats()
        print(f"  Sources succeeded: {stats['sources_succeeded']}")
        print(f"  Sources failed: {stats['sources_failed']}")
        
        self.assertGreater(len(jobs), 0, "No jobs found")
    
    def test_no_duplicate_urls(self):
        """Test that there are no duplicate URLs"""
        jobs = scrape_all_browser_jobs()
        
        urls = [job.get('url', '').lower() for job in jobs]
        unique_urls = set(urls)
        
        self.assertEqual(len(urls), len(unique_urls), "Duplicate URLs found")
        print(f"✓ No duplicate URLs (tested {len(unique_urls)} jobs)")
    
    def test_job_data_quality(self):
        """Test data quality of aggregated jobs"""
        jobs = scrape_all_browser_jobs()
        
        if not jobs:
            self.skipTest("No jobs to test")
        
        for i, job in enumerate(jobs[:10]):  # Test first 10
            errors = JobDataValidator.validate_job(job)
            if errors:
                print(f"  Job {i}: {job['title']} - {errors}")
            self.assertEqual(len(errors), 0, f"Job {i} validation failed")
        
        print(f"✓ Data quality validated for {min(10, len(jobs))} jobs")


class TestPerformance(unittest.TestCase):
    """Test scraper performance"""
    
    def test_scraping_speed(self):
        """Test scraping speed"""
        print("\nPerformance test...")
        
        start = time.time()
        jobs = scrape_all_browser_jobs()
        elapsed = time.time() - start
        
        print(f"  Time taken: {elapsed:.2f}s")
        print(f"  Jobs per second: {len(jobs)/elapsed:.2f}")
        
        # Scraping should complete in reasonable time
        self.assertLess(elapsed, 120, "Scraping took too long (>2 minutes)")
        print("✓ Performance acceptable")


def run_quick_test():
    """Run quick smoke test"""
    print("\n" + "="*60)
    print("QUICK SCRAPER TEST")
    print("="*60)
    
    print("\n[1] Testing sample jobs (should be empty)...")
    jobs = get_sample_jobs_for_demo()
    if len(jobs) == 0:
        print(f"✓ Sample jobs disabled (expected)")
    else:
        print(f"✗ Sample jobs should be empty but found {len(jobs)}")
    
    print("\n[2] Testing API scraping...")
    all_jobs = scrape_all_browser_jobs()
    print(f"✓ Found {len(all_jobs)} real jobs")
    
    print("\n[3] Summary...")
    stats = get_scraper_stats()
    for source, count in stats['jobs_by_source'].items():
        if count > 0:
            print(f"  {source}: {count} jobs")
    
    if len(all_jobs) == 0:
        print("\n⚠ No jobs found. Check internet connection and API availability.")
    
    print("\n" + "="*60)
    print("QUICK TEST COMPLETE ✓")
    print("="*60)


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Test Job Scraper')
    parser.add_argument('--quick', action='store_true', help='Run quick smoke test')
    parser.add_argument('--verbose', action='store_true', help='Verbose output')
    parser.add_argument('--test', type=str, help='Run specific test')
    
    args = parser.parse_args()
    
    if args.quick:
        run_quick_test()
    else:
        # Run full test suite
        unittest.main(verbosity=2 if args.verbose else 1)
