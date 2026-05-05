#!/usr/bin/env python3
"""LinkedIn Scraper for ServiceNow jobs"""

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


class LinkedInScraper:
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.base_url = "https://www.linkedin.com/jobs/search/"

    def scrape_jobs(self) -> List[Job]:
        """Scrape job listings from LinkedIn"""
        jobs = []
        
        try:
            # Search for ServiceNow jobs in the UK
            params = {
                "keywords": "ServiceNow",
                "location": "United Kingdom",
                "trk": "homepage-jobseeker_jobs-search-bar_search-submit",
                "position": 1
            }
            
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                'Accept-Language': 'en-US,en;q=0.5',
                'Referer': 'https://www.linkedin.com/',
                'DNT': '1',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Dest': 'document',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-Site': 'none',
                'Cache-Control': 'max-age=0',
            }
            
            response = requests.get(self.base_url, params=params, headers=headers, timeout=30)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # LinkedIn job extraction logic would go here
            # This is a placeholder since LinkedIn has anti-scraping measures
            
            print(f"LinkedIn scrape: {len(jobs)} jobs found")
            
        except requests.RequestException as e:
            print(f"Error fetching LinkedIn jobs: {e}")
        
        return jobs

    def save_to_db(self, jobs: List[Job]):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
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
        jobs = self.scrape_jobs()
        self.save_to_db(jobs)
        return jobs

if __name__ == "__main__":
    from job_model import Job
    scraper = LinkedInScraper()
    jobs = scraper.run()
    print(f"Found {len(jobs)} jobs from LinkedIn")