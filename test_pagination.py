#!/usr/bin/env python3
"""
Test paginated API endpoint
"""
import requests
import json

API_URL = 'http://localhost:5000/api/jobs'

def test_pagination():
    """Test pagination API"""
    
    print("Testing Pagination API Endpoint\n")
    print("=" * 60)
    
    # Test page 1
    print("\n📄 Fetching Page 1...")
    response = requests.get(f'{API_URL}?page=1')
    data = response.json()
    
    print(f"✓ Status: {response.status_code}")
    print(f"✓ Jobs on page: {len(data['jobs'])}")
    print(f"✓ Pagination Info:")
    print(f"  - Current Page: {data['pagination']['current_page']}")
    print(f"  - Total Pages: {data['pagination']['total_pages']}")
    print(f"  - Total Jobs: {data['pagination']['total_jobs']}")
    print(f"  - Jobs per Page: {data['pagination']['jobs_per_page']}")
    print(f"  - Has Next: {data['pagination']['has_next']}")
    print(f"  - Has Prev: {data['pagination']['has_prev']}")
    
    if data['jobs']:
        print(f"\n✓ Sample Jobs on Page 1:")
        for i, job in enumerate(data['jobs'][:3], 1):
            print(f"  {i}. {job['title']} @ {job['company']}")
    
    # Test page 2 if available
    if data['pagination']['has_next']:
        print("\n📄 Fetching Page 2...")
        response2 = requests.get(f'{API_URL}?page=2')
        data2 = response2.json()
        
        print(f"✓ Status: {response2.status_code}")
        print(f"✓ Jobs on page: {len(data2['jobs'])}")
        print(f"✓ Current Page: {data2['pagination']['current_page']}")
        
        if data2['jobs']:
            print(f"\n✓ Sample Jobs on Page 2:")
            for i, job in enumerate(data2['jobs'][:3], 1):
                print(f"  {i}. {job['title']} @ {job['company']}")
    
    # Test with filters
    print("\n📄 Fetching Page 1 with UI/UX filter...")
    response3 = requests.get(f'{API_URL}?page=1&role=UI/UX')
    data3 = response3.json()
    
    print(f"✓ Status: {response3.status_code}")
    print(f"✓ UI/UX Jobs found: {data3['pagination']['total_jobs']}")
    print(f"✓ Total Pages: {data3['pagination']['total_pages']}")
    print(f"✓ Jobs on this page: {len(data3['jobs'])}")
    
    print("\n" + "=" * 60)
    print("✓ Pagination API Tests Complete!")

if __name__ == '__main__':
    test_pagination()
