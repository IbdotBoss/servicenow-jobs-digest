#!/usr/bin/env python3
"""Indeed Scraper for ServiceNow jobs"""

import sys
import os
# Add project root to path to enable absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
import sqlite3
import json
import os
from typing import Optional, List, Dict, Any

from job_model import Job


class IndeedScraper:
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.base_url = "https://www.indeed.com/jobs"

    def scrape_jobs(self) -> List[Job]:
        """Scrape job listings from Indeed"""
        jobs = []
        
        try:
            # Search for ServiceNow jobs in the UK
            query = {
                "q": "ServiceNow",
                "l": "United Kingdom",
                "radius": 50,
                "fromage": "7",  # Past week
                "limit": 50
            }
            
            # Use better headers to mimic a browser
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.indeed.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            response = requests.get(self.base_url, params=query, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all('div', class_='jobsearch-SerpJobCard')
            
            for card in job_cards:
                try:
                    title_elem = card.find('a', class_='jobtitle')
                    company_elem = card.find('span', class_='company')
                    location_elem = card.find('span', class_='location')
                    link_elem = card.find('a', class_='jobtitle')
                    
                    if not all([title_elem, company_elem, location_elem, link_elem]):
                        continue
                        
                    title = title_elem.text.strip()
                    company = company_elem.text.strip()
                    location = location_elem.text.strip()
                    link = "https://www.indeed.com" + link_elem['href']
                    
                    # Check if job is relevant (ServiceNow related)
                    if "service-now" not in title.lower() and "servicenow" not in title.lower():
                        continue
                        
                    # Create Job object
                    job = Job(
                        title=title,
                        company=company,
                        location=location,
                        link=link,
                        source="Indeed",
                        timestamp=datetime.now().isoformat()
                    )
                    jobs.append(job)
                    
                except Exception as e:
                    print(f"Error parsing Indeed job card: {e}")
                    continue
                    
        except requests.RequestException as e:
            print(f"Error fetching Indeed jobs: {e}")
        
        return jobs

    def save_to_db(self, jobs: List[Job]):
        """Save jobs to SQLite database with deduplication"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Create table if not exists
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                title TEXT NOT NULL,
                company TEXT,
                location TEXT,
                link TEXT UNIQUE,
                source TEXT,
                timestamp TEXT,
                visa_sponsorship TEXT,
                remote_work TEXT
            )
        ''')
        
        # Insert or ignore duplicates
        for job in jobs:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO jobs 
                    (title, company, location, link, source, timestamp, visa_sponsorship, remote_work)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job.title, job.company, job.location, job.link, job.source,
                    job.timestamp, job.visa_sponsorship, job.remote_work
                ))
            except sqlite3.Error as e:
                print(f"Error inserting job {job.link}: {e}")
        
        conn.commit()
        conn.close()

    def run(self) -> List[Job]:
        """Run the scraper and save results"""
        jobs = self.scrape_jobs()
        self.save_to_db(jobs)
        return jobs

if __name__ == "__main__":
    scraper = IndeedScraper()
    jobs = scraper.run()
    print(f"Found {len(jobs)} jobs from Indeed")