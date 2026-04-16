#!/usr/bin/env python3
"""
Add test jobs to the database to test pagination
"""
import sqlite3
from datetime import datetime, timedelta
import random

DB_PATH = 'jobs.db'

test_jobs = [
    ("UI/UX Designer Internship", "Tech Startup", "Toronto", "UI/UX"),
    ("Junior UX Researcher", "Innovation Labs", "Ottawa", "Research"),
    ("Data Analyst Co-op", "Finance Corp", "Mississauga", "Analyst"),
    ("Entry Level UI Developer", "Digital Agency", "Waterloo", "UI/UX"),
    ("Research Intern", "University Research", "Guelph", "Research"),
    ("Business Analyst", "Consulting Firm", "Toronto", "Analyst"),
    ("UX/UI Designer", "E-commerce Platform", "Kitchener", "UI/UX"),
    ("Junior Analyst", "Market Research", "Ottawa", "Analyst"),
    ("UX Research Assistant", "Tech Giants", "Mississauga", "Research"),
    ("UI Design Intern", "Startup Studio", "Toronto", "UI/UX"),
    ("Entry-level Researcher", "Think Tank", "Waterloo", "Research"),
    ("Data Analysis Intern", "Retail Chain", "Guelph", "Analyst"),
    ("UX Designer Co-op", "Software Company", "Ottawa", "UI/UX"),
    ("Junior Research Analyst", "Consulting", "Toronto", "Research"),
    ("Analytics Intern", "Tech Company", "Mississauga", "Analyst"),
    ("UI/UX Developer", "Design Studio", "Waterloo", "UI/UX"),
    ("Research Specialist (Entry)", "University", "Guelph", "Research"),
    ("Business Analyst Intern", "Finance", "Toronto", "Analyst"),
    ("Assistant UX Designer", "Creative Agency", "Ottawa", "UI/UX"),
    ("Junior Data Analyst", "Tech Startup", "Mississauga", "Analyst"),
    ("UX Researcher Intern", "Innovation Hub", "Kitchener", "Research"),
    ("UI Designer Entry Level", "App Developer", "Toronto", "UI/UX"),
    ("Research Associate", "Market Research", "Waterloo", "Research"),
    ("Analysis Assistant", "Consulting Group", "Guelph", "Analyst"),
    ("UX/UI Intern", "Digital Marketing", "Ottawa", "UI/UX"),
    ("Junior Researcher", "Education Tech", "Toronto", "Research"),
    ("Data Analyst Apprentice", "Banking", "Mississauga", "Analyst"),
    ("UI Developer (Entry)", "Fintech Startup", "Waterloo", "UI/UX"),
    ("Research Intern (Paid)", "Healthcare Tech", "Guelph", "Research"),
    ("Business Analyst Co-op", "Manufacturing", "Toronto", "Analyst"),
    ("Associate UX Designer", "SaaS Company", "Ottawa", "UI/UX"),
    ("Research Assistant (Part-time)", "Academic", "Mississauga", "Research"),
    ("Analyst - Early Career", "Logistics", "Kitchener", "Analyst"),
    ("UI/UX Designer Apprentice", "Web Agency", "Toronto", "UI/UX"),
    ("Junior Researcher (Contract)", "Tech Research", "Waterloo", "Research"),
]

locations = ["Toronto", "Ottawa", "Mississauga", "Waterloo", "Guelph", "Kitchener"]
roles = ["UI/UX", "Research", "Analyst"]

def add_test_jobs():
    """Add test jobs to database"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    # Add more jobs to ensure we have enough for pagination testing
    added = 0
    for i, (title, company, location, role) in enumerate(test_jobs):
        try:
            # Check if job already exists
            c.execute('''
                SELECT id FROM jobs 
                WHERE title = ? AND company = ? AND url = ?
            ''', (title, company, f'https://example.com/job-{i}'))
            
            if not c.fetchone():
                # Generate a date 0-30 days in the past
                posted_days_ago = random.randint(0, 30)
                posted_date = (datetime.now() - timedelta(days=posted_days_ago)).isoformat()
                
                # Determine if it's a student job based on title
                is_student = 1 if any(kw in title.lower() for kw in ['intern', 'entry', 'junior', 'co-op', 'apprentice', 'assistant']) else 0
                
                # Generate salary info
                salaries = ['$17-20/hour', '$18-22/hour', '$20-25/hour', 'Competitive', 'TBD', '$50k-60k/year']
                salary = random.choice(salaries)
                
                description = f"Join our team as a {role} professional. We're looking for talented individuals to help us innovate and create amazing products."
                
                c.execute('''
                    INSERT INTO jobs (title, company, location, role, description, url, posted_date, salary, is_student_job)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    title,
                    company,
                    location,
                    role,
                    description,
                    f'https://example.com/job-{i}',
                    posted_date,
                    salary,
                    is_student
                ))
                added += 1
                print(f"✓ Added: {title} at {company}")
        except Exception as e:
            print(f"✗ Error adding {title}: {str(e)}")
    
    conn.commit()
    conn.close()
    
    print(f"\n✓ Successfully added {added} test jobs to the database")

if __name__ == '__main__':
    add_test_jobs()
