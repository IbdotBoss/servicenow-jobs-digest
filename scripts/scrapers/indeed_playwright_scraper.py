#!/usr/bin/env python3
"""Indeed Scraper using Playwright"""

import sys
import os
# Add project root to path to enable absolute imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

from bs4 import BeautifulSoup
from job_model import Job

from playwright.async_api import async_playwright


class IndeedPlaywrightScraper:
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.jobs = []

    async def initialize(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await self.context.new_page()
        
        # Set realistic fingerprints
        await self.page.set_extra_http_headers({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.google.com/',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        await self.page.set_viewport_size({'width': 1920, 'height': 1080})

    async def close(self):
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def scrape_jobs(self):
        try:
            await self.page.goto("https://www.indeed.com/jobs?q=ServiceNow&l=United+Kingdom", timeout=30000)
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(10)
            
            content = await self.page.content()
            print(f"Indeed page length: {len(content)} characters")
            with open('/tmp/indeed_page.html', 'w') as f:
                f.write(content)
            print("Indeed page saved to /tmp/indeed_page.html")
            
            soup = BeautifulSoup(content, 'html.parser')
            job_cards = soup.find_all('div', class_='jobsearch-SerpJobCard')
            print(f"Found {len(job_cards)} job cards")
            
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
                    
                    if "service-now" not in title.lower() and "servicenow" not in title.lower():
                        continue
                    
                    job = Job(
                        title=title,
                        company=company,
                        location=location,
                        link=link,
                        source="Indeed",
                        timestamp=datetime.now().isoformat()
                    )
                    self.jobs.append(job)
                    print(f"✅ Found job: {title} at {company}")
                    
                except Exception as e:
                    print(f"Error parsing Indeed job card: {e}")
                    continue
            
        except Exception as e:
            print(f"Error scraping Indeed: {e}")
            import traceback
            traceback.print_exc()
        
        return self.jobs

    async def save_to_db(self, jobs):
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

    async def run(self):
        try:
            await self.initialize()
            jobs = await self.scrape_jobs()
            await self.save_to_db(jobs)
            return jobs
        finally:
            await self.close()


if __name__ == "__main__":
    from job_model import Job
    scraper = IndeedPlaywrightScraper()
    jobs = asyncio.run(scraper.run())
    print(f"Found {len(jobs)} jobs from Indeed")