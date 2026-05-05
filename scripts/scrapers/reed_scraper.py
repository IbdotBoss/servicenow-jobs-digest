#!/usr/bin/env python3
"""
Reed.co.uk Scraper using API endpoint
"""

import asyncio
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from playwright.async_api import async_playwright

from ..job_model import Job

class ReedScraper:
    async def scrape_jobs(self) -> List[Job]:
        jobs = []
        try:
            # Use Playwright to make the API request with proper headers
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage']
            )
            context = await browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            page = await context.new_page()
            
            # Set headers to mimic a real browser
            await page.set_extra_http_headers({
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'application/json',
                'Referer': 'https://www.reed.co.uk/jobs/jobs-in-united-kingdom?q=ServiceNow',
            })
            
            # Build API URL
            base_url = "https://www.reed.co.uk/jobs/jobs-in-united-kingdom"
            params = {
                "q": "ServiceNow",
                "format": "rss",
            }
            url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
            
            print(f"Fetching job data from API: {url}")
            
            # Handle rate limiting with retries
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = await page.goto(url, timeout=30000)
                    if response:
                        status = response.status
                        print(f"API response status: {status}")
                        if status == 200:
                            body = await response.text()
                            try:
                                # Parse the HTML content to extract job data
                                soup = BeautifulSoup(body, 'html.parser')
                                job_items = soup.find_all('item')
                                print(f"Found {len(job_items)} job items")
                                
                                for job_item in job_items[:50]:
                                    try:
                                        title = job_item.title.text if job_item.title else ''
                                        if not any(kw in title.lower() for kw in ['service-now', 'servicenow', 'service now']):
                                            continue
                                            
                                        company = job_item.find('recruiter').text if job_item.find('recruiter') else ''
                                        location = job_item.find('location').text if job_item.find('location') else ''
                                        link = job_item.link.text if job_item.link else ''
                                        
                                        job = Job(
                                            title=title,
                                            company=company,
                                            location=location,
                                            link=link,
                                            source="Reed",
                                            timestamp=datetime.now().isoformat()
                                        )
                                        jobs.append(job)
                                        print(f"✅ Found job: {title} at {company}")
                                    except Exception as e:
                                        print(f"Error processing job item: {e}")
                                break  # Success, break retry loop
                            except json.JSONDecodeError:
                                print(f"Failed to parse JSON: {body[:500]}...")
                                break
                        elif status == 429:  # Too Many Requests
                            print(f"Rate limited. Attempt {attempt + 1}/{max_retries}. Waiting 10 seconds...")
                            await asyncio.sleep(10)
                        else:
                            print(f"Error: {await response.text()[:500]}")
                            break
                    else:
                        print("No response from API")
                        break
                except Exception as e:
                    print(f"Request failed: {e}")
                    await asyncio.sleep(5)
            
            await browser.close()
            await playwright.stop()
            
        except Exception as e:
            print(f"Error scraping Reed: {e}")
            
        return jobs

    async def save_to_db(self, jobs: List[Job]):
        conn = sqlite3.connect("jobs.db")
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
            except Exception as e:
                print(f"Error inserting job {job.link}: {e}")
                
        conn.commit()
        conn.close()
        
    async def run(self):
        """Run the scraper and save results"""
        try:
            jobs = await self.scrape_jobs()
            await self.save_to_db(jobs)
            return jobs
        except Exception as e:
            print(f"Error in ReedScraper.run: {e}")
            return []

if __name__ == "__main__":
    from ..job_model import Job
    scraper = ReedScraper()
    jobs = asyncio.run(scraper.run())
    print(f"Found {len(jobs)} jobs from Reed")