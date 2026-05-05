#!/usr/bin/env python3
"""
LinkedIn Job Scraper
- Scrapes ServiceNow jobs from LinkedIn with UK filter
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from job_model import Job, parse_date, normalize_location, extract_tags

LINKEDIN_SEARCH_URL = "https://www.linkedin.com/jobs/search"

def scrape_linkedin() -> list[Job]:
    """Scrape ServiceNow jobs from LinkedIn"""
    jobs = []
    
    params = {
        "keywords": "ServiceNow",
        "location": "United Kingdom",
        "trk": "jobs_search_button",
        "f_TP": "1"  # Full time only
    }
    
    try:
        # Need to handle cookies and potential login requirements
        # For now, use a simple approach with headers
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
        }
        
        response = requests.get(LINKEDIN_SEARCH_URL, params=params, headers=headers, timeout=30)
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # LinkedIn's structure is complex and often requires JavaScript
            # For now, we'll parse what we can from the static HTML
            job_elements = soup.find_all('li', class_=re.compile(r'job-card|job-item'))
            
            for element in job_elements[:10]:  # Limit due to complexity
                try:
                    job = parse_job_element(element)
                    if job:
                        job.source = "linkedin"
                        job.sponsorship_confirmed = False  # LinkedIn doesn't verify sponsorship
                        jobs.append(job)
                except Exception as e:
                    continue
                    
    except Exception as e:
        print(f"[LinkedIn] Failed to scrape: {e}")
    
    print(f"[LinkedIn] Scraped {len(jobs)} jobs")
    return jobs

def parse_job_element(element) -> Optional[Job]:
    """Parse a LinkedIn job element"""
    
    # Job title
    title_elem = element.find('h2') or element.find('h3')
    if not title_elem:
        return None
    
    title = title_elem.get_text(strip=True)
    
    # Job link
    link_elem = element.find('a', href=True)
    link = link_elem['href'] if link_elem else ""
    if link and not link.startswith('http'):
        link = f"https://www.linkedin.com{link}"
    
    # Company
    company_elem = element.find('span', class_=re.compile(r'company|org'))
    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
    
    # Location
    location_elem = element.find('span', class_=re.compile(r'location|place'))
    location = location_elem.get_text(strip=True) if location_elem else "UK"
    
    # Date posted - often in a small text
    date_elem = element.find('span', class_=re.compile(r'date|posted'))
    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%Y-%m-%d")
    
    # Clean date string
    date_str = re.sub(r' ago', '', date_str)
    date = parse_date(date_str)
    
    job = Job(
        title=title,
        company=company,
        location=normalize_location(location),
        date=date,
        link=link,
        tags=extract_tags(title, "")
    )
    
    return job

if __name__ == "__main__":
    jobs = scrape_linkedin()
    for job in jobs[:3]:
        print(f"LinkedIn: {job.title} at {job.company}")