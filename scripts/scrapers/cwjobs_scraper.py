#!/usr/bin/env python3
"""CWJobs Scraper using Playwright"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio
import sqlite3
from datetime import datetime
from typing import List, Dict, Any, Optional

from job_model import Job

from playwright.async_api import async_playwright


class CWJobsScraper:
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
            'Accept-Language': 'en-GB,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
            'Sec-Ch-Ua': '"Chromium";v="120", "Google Chrome";v="120", "Chromium WebView";v="120"',
            'Sec-Ch-Ua-Mobile': '?0',
            'Sec-Ch-Ua-Platform': '"Windows NT 10.0"',
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
            # Search URL for ServiceNow jobs
            search_url = "https://www.cwjobs.co.uk/jobs/servicenow"
            print(f"[CWJobs] Navigating to: {search_url}")
            
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_load_state('load')
            await asyncio.sleep(10)  # Wait for JavaScript to execute
            
            # Get page content
            content = await self.page.content()
            print(f"[CWJobs] Page length: {len(content)} characters")
            
            # Save for debugging
            with open('/tmp/cwjobs_page.html', 'w') as f:
                f.write(content)
            print("[CWJobs] Page saved to /tmp/cwjobs_page.html")
            
            # Parse with BeautifulSoup
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(content, 'html.parser')
            
            # Find job cards
            job_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                kw in x.lower() 
                for kw in ['job-result', 'job-card', 'job-item', 'search-result', 'job-cta', 'job-list-item']
            ))
            print(f"[CWJobs] Found {len(job_cards)} job cards")
            
            for card in job_cards[:50]:  # Limit to first 50
                try:
                    # Extract title
                    title_elem = card.find('a', class_=lambda x: x and 'title' in x.lower() if x else False)
                    if not title_elem:
                        title_elem = card.find('h2') or card.find('h3')
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    
                    # Check for ServiceNow keyword
                    if not any(kw in title.lower() for kw in ['servicenow', 'service-now', 'service now']):
                        continue
                    
                    # Extract company
                    company_elem = card.find('span', class_=lambda x: x and 'company' in x.lower() if x else False)
                    if not company_elem:
                        company_elem = card.find('div', class_=lambda x: x and 'company' in x.lower() if x else False)
                    company = company_elem.text.strip() if company_elem else ''
                    
                    # Extract location
                    location_elem = card.find('span', class_=lambda x: x and 'location' in x.lower() if x else False)
                    location = location_elem.text.strip() if location_elem else ''
                    
                    # Extract link
                    link_elem = card.find('a', href=True)
                    if not link_elem:
                        continue
                    
                    link = link_elem['href']
                    if not link.startswith('http'):
                        link = f"https://www.cwjobs.co.uk{link}"
                    
                    # Create Job object
                    job = Job(
                        title=title,
                        company=company,
                        location=location,
                        link=link,
                        source="CWJobs",
                        date=datetime.now().strftime("%Y-%m-%d"),
                        sponsorship_confirmed=True,
                        remote_work="Not specified"
                    )
                    self.jobs.append(job)
                    print(f"✅ Found job: {title} at {company}")
                    
                except Exception as e:
                    print(f"Error parsing CWJobs card: {e}")
                    continue
            
        except Exception as e:
            print(f"Error scraping CWJobs: {e}")
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
                sponsorship_confirmed BOOLEAN DEFAULT 0,
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
                    job.date, job.sponsorship_confirmed, job.remote_work
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
    scraper = CWJobsScraper()
    jobs = asyncio.run(scraper.run())
    print(f"Found {len(jobs)} jobs from CWJobs")
