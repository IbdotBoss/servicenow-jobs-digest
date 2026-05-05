#!/usr/bin/env python3
"""
Hunt UK Scraper using Playwright (headless browser)
"""

import asyncio
import sqlite3
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

from ..job_model import Job

class HuntUKPlaywrightScraper:
    def __init__(self, db_path: str = "jobs.db"):
        self.db_path = db_path
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.jobs = []
        
    async def initialize(self):
        """Initialize Playwright and browser"""
        import asyncio
        from playwright.async_api import async_playwright
        
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=True,
            args=['--no-sandbox', '--disable-dev-shm-usage']
        )
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080}
        )
        self.page = await self.context.new_page()
        
        # Set up response handler
        def handle_response(response):
            asyncio.create_task(self.process_response(response))
            
        self.page.on("response", handle_response)
        
    async def close(self):
        """Close browser and Playwright"""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
            
    async def scrape_jobs(self):
        """Scrape job listings from Hunt UK"""
        try:
            # Navigate to Hunt UK site
            await self.page.goto("https://huntukvisasponsors.com/jobs", timeout=30000)
            
            # Wait for page to load and JavaScript to execute
            await self.page.wait_for_load_state('networkidle', timeout=30000)
            
            # Wait a bit more for dynamic content to render
            await asyncio.sleep(5)
            
            print(f"Found {len(self.jobs)} ServiceNow jobs so far")
            
        except Exception as e:
            print(f"Error scraping Hunt UK: {e}")
            import traceback
            traceback.print_exc()
            
        return self.jobs
        
    async def process_response(self, response):
        """Process a response to check for job data"""
        try:
            # Check if this is a JSON response
            content_type = response.headers.get('content-type', '')
            if 'application/json' not in content_type:
                return
                
            # Get the request URL
            request = await response.request()
            url = request.url
            
            print(f"Checking response from: {url}")
            
            # Read the response body
            body = await response.body()
            try:
                json_data = json.loads(body)
                self.extract_jobs_from_json(json_data, self.jobs)
            except json.JSONDecodeError:
                # Not valid JSON
                pass
                
        except Exception as e:
            # Ignore errors
            pass
            
    def extract_jobs_from_json(self, data: Any, jobs: List[Job]):
        """Recursively extract job postings from JSON data"""
        if isinstance(data, dict):
            # Check if this is a JobPosting
            if data.get('@type') == 'JobPosting':
                try:
                    title = data.get('title', '')
                    if title and self.is_servicenow_job(title):
                        job = self.create_job_from_json_ld(data)
                        if job:
                            jobs.append(job)
                            print(f"✅ Found ServiceNow job: {title}")
                except Exception as e:
                    print(f"Error parsing JobPosting: {e}")
                return
                
            # Check if this is an ItemList containing job items
            if data.get('@type') == 'ItemList':
                items = data.get('itemListElement', [])
                for item in items:
                    if isinstance(item, dict) and item.get('@type') == 'ListItem':
                        item_job = item.get('item')
                        if isinstance(item_job, dict) and item_job.get('@type') == 'JobPosting':
                            try:
                                title = item_job.get('title', '')
                                if title and self.is_servicenow_job(title):
                                    job = self.create_job_from_json_ld(item_job)
                                    if job:
                                        jobs.append(job)
                                        print(f"✅ Found ServiceNow job from ItemList: {title}")
                            except Exception as e:
                                print(f"Error parsing JobPosting from ItemList: {e}")
                return
                
            # Recursively search in dictionary values
            for value in data.values():
                self.extract_jobs_from_json(value, jobs)
                
        elif isinstance(data, list):
            # Recursively search in list items
            for item in data:
                self.extract_jobs_from_json(item, jobs)
                
    def create_job_from_json_ld(self, json_ld: dict) -> Optional[Job]:
        """Create a Job object from JSON-LD data"""
        try:
            title = json_ld.get('title', '')
            if not title:
                return None
                
            company = json_ld.get('hiringOrganization', {}).get('name', '')
            if not company:
                # Try to find company name in other fields
                employer = json_ld.get('employer', {})
                if isinstance(employer, dict):
                    company = employer.get('name', '')
                else:
                    company = employer
                    
            location = json_ld.get('jobLocation', [{}])[0].get('address', {}).get('addressLocality', '')
            if not location:
                location = json_ld.get('jobLocation', [{}])[0].get('address', {}).get('addressRegion', '')
                
            link = json_ld.get('url', '')
            if not link.startswith('http'):
                # Try to construct full URL
                if link.startswith('/'):
                    link = f"https://huntukvisasponsors.com{link}"
                else:
                    link = f"https://huntukvisasponsors.com/{link}"
                
            return Job(
                title=title,
                company=company,
                location=location,
                link=link,
                source="Hunt UK",
                timestamp=datetime.now().isoformat()
            )
        except Exception as e:
            print(f"Error creating job from JSON-LD: {e}")
            return None
            
    def is_servicenow_job(self, title: str) -> bool:
        """Check if the job is ServiceNow related"""
        servcenoa_keywords = ['service-now', 'servicenow', 'service now', 'service_now']
        title_lower = title.lower()
        return any(keyword in title_lower for keyword in servcenoa_keywords)
        
    async def save_to_db(self, jobs: List[Job]):
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
        
    async def run(self):
        """Run the scraper and save results"""
        try:
            await self.initialize()
            jobs = await self.scrape_jobs()
            await self.save_to_db(jobs)
            return jobs
        finally:
            await self.close()

if __name__ == "__main__":
    from ..job_model import Job
    scraper = HuntUKPlaywrightScraper()
    jobs = scraper.run()
    print(f"Found {len(jobs)} jobs from Hunt UK")