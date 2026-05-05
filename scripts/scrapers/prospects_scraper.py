#!/usr/bin/env python3
"""Prospects Scraper using Playwright"""

import asyncio
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from scripts.job_model import Job
from playwright.async_api import async_playwright

class ProspectsScraper:
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
            await self.initialize()
            
            search_url = "https://www.prospects.ac.uk/jobs/servicenow"
            print(f"[Prospects] Navigating to: {search_url}")
            
            await self.page.goto(search_url, timeout=30000)
            await self.page.wait_for_load_state('load')
            await asyncio.sleep(10)  # Wait for JavaScript to execute
            await asyncio.sleep(5)
            
            content = await self.page.content()
            print(f"[Prospects] Page length: {len(content)} characters")
            
            with open('/tmp/prospects_page.html', 'w') as f:
                f.write(content)
            print("[Prospects] Page saved to /tmp/prospects_page.html")
            
            soup = BeautifulSoup(content, 'html.parser')
            
            job_cards = soup.find_all(['div', 'article'], class_=lambda x: x and any(
                kw in x.lower() 
                for kw in ['job', 'vacancy', 'listing', 'result-item', 'card', 'item']
            ))
            print(f"[Prospects] Found {len(job_cards)} job cards")
            
            for card in job_cards[:50]:
                try:
                    title_elem = card.find('a', class_=lambda x: x and 'title' in x.lower() if x else False)
                    if not title_elem:
                        title_elem = card.find('h2') or card.find('h3')
                    if not title_elem:
                        continue
                    
                    title = title_elem.text.strip()
                    
                    if not any(kw in title.lower() for kw in ['servicenow', 'service-now', 'service now']):
                        continue
                    
                    company_elem = card.find('span', class_=lambda x: x and 'company' in x.lower() if x else False)
                    if not company_elem:
                        company_elem = card.find('div', class_=lambda x: x and 'company' in x.lower() if x else False)
                    company = company_elem.text.strip() if company_elem else ''
                    
                    location_elem = card.find('span', class_=lambda x: x and 'location' in x.lower() if x else False)
                    location = location_elem.text.strip() if location_elem else ''
                    
                    link_elem = card.find('a', href=True)
                    if not link_elem:
                        continue
                    
                    link = link_elem['href']
                    if not link.startswith('http'):
                        link = f"https://www.prospects.ac.uk{link}"
                    
                    job = Job(
                        title=title,
                        company=company,
                        location=location,
                        link=link,
                        source="Prospects",
                        date=datetime.now().strftime("%Y-%m-%d"),
                        sponsorship_confirmed=True,
                        remote_work="Not specified"
                    )
                    self.jobs.append(job)
                    print(f"✅ Found job: {title} at {company}")
                    
                except Exception as e:
                    print(f"Error parsing Prospects card: {e}")
                    continue
            
            await self.close()
            
        except Exception as e:
            print(f"Error scraping Prospects: {e}")
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
                date TEXT,
                sponsorship_confirmed BOOLEAN DEFAULT 0,
                remote_work TEXT
            )
        ''')
        
        for job in jobs:
            try:
                cursor.execute('''
                    INSERT OR IGNORE INTO jobs 
                    (title, company, location, link, source, date, sponsorship_confirmed, remote_work)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    job.title, job.company, job.location, job.link, job.source,
                    job.date, job.sponsorship_confirmed, job.remote_work
                ))
            except sqlite3.Error as e:
                print(f"Error inserting job {job.link}: {e}")
        
        conn.commit()


    async def run(self):
        try:
            jobs = await self.scrape_jobs()
            await self.save_to_db(jobs)
            return jobs
        except Exception as e:
            print(f"Error in ProspectsScraper.run: {e}")
            import traceback
            traceback.print_exc()
            return []
