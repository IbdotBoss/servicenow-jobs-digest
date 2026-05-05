#!/usr/bin/env python3
"""
Indeed UK Scraper for ServiceNow jobs
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from job_model import Job, parse_date, normalize_location, extract_tags

def scrape() -> list[Job]:
    """Scrape Indeed UK for ServiceNow jobs"""
    jobs = []
    base_url = "https://www.indeed.co.uk"
    
    params = {
        "q": "ServiceNow",
        "l": "United Kingdom",
        "sort": "date",
        "fromage": "7"
    }
    
    try:
        response = requests.get(
            base_url, 
            params=params, 
            headers={'User-Agent': 'Mozilla/5.0'}, 
            timeout=30
        )
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        job_cards = soup.find_all('div', class_=re.compile(r'jobsearch-SerpJobCard|job_card'))
        
        for card in job_cards[:20]:
            try:
                job = parse_job(card)
                if job:
                    job.source = "indeed"
                    job.sponsorship_confirmed = False
                    jobs.append(job)
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"[Indeed] Error: {e}")
    
    return jobs

def parse_job(card) -> Optional[Job]:
    """Parse an Indeed job card"""
    
    # Title
    title_elem = card.find('h2', class_=re.compile(r'title|jobTitle'))
    if not title_elem:
        return None
    title_elem = title_elem.find('a') or title_elem
    title = title_elem.get_text(strip=True)
    
    # Link
    link_elem = card.find('a', href=True)
    if not link_elem:
        return None
    link = "https://www.indeed.co.uk" + link_elem['href']
    
    # Company
    company_elem = card.find('span', class_=re.compile(r'company|companyName'))
    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
    
    # Location
    location_elem = card.find('span', class_=re.compile(r'location|workLocation'))
    location = location_elem.get_text(strip=True) if location_elem else "UK"
    
    # Date posted
    date_elem = card.find('span', class_=re.compile(r'date|jobAge'))
    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%Y-%m-%d")
    
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
    jobs = scrape()
    print(f"Indeed: {len(jobs)} jobs scraped")
    for job in jobs[:3]:
        print(f"- {job.title} at {job.company}")