#!/usr/bin/env python3
"""
Hunt UK Visa Sponsors Scraper
- Scrapes ServiceNow jobs from huntukvisasponsors.com
- Extracts job title, company, location, date, and link
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from job_model import Job, parse_date, normalize_location, extract_tags

HUNT_UK_URL = "https://huntukvisasponsors.com"

def scrape_hunt_uk() -> list[Job]:
    """Scrape ServiceNow jobs from Hunt UK"""
    jobs = []
    
    try:
        # Search for ServiceNow jobs
        search_url = f"{HUNT_UK_URL}/job/search/?search=servicenow"
        response = requests.get(search_url, timeout=30)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Find all job listings
        # The structure may vary - need to inspect the actual page
        job_elements = soup.find_all('div', class_=re.compile(r'job-listing|job-item'))
        
        if not job_elements:
            # Try alternative selectors
            job_elements = soup.find_all('article')
        
        print(f"[Hunt UK] Found {len(job_elements)} job elements")
        
        for element in job_elements[:20]:  # Limit to first 20
            try:
                job = parse_job_element(element)
                if job:
                    jobs.append(job)
            except Exception as e:
                print(f"[Hunt UK] Error parsing job element: {e}")
                continue
                
    except Exception as e:
        print(f"[Hunt UK] Failed to scrape: {e}")
    
    print(f"[Hunt UK] Successfully scraped {len(jobs)} ServiceNow jobs")
    return jobs

def parse_job_element(element) -> Optional[Job]:
    """Parse a single job element into Job object"""
    
    # Extract job title
    title_elem = element.find('h2') or element.find('h3') or element.find('a', class_=re.compile(r'title|job-title'))
    if not title_elem:
        return None
    
    title = title_elem.get_text(strip=True)
    
    # Extract link
    link_elem = element.find('a', href=True)
    if link_elem:
        link = link_elem['href']
        # Make absolute URL if relative
        if link.startswith('/'):
            link = HUNT_UK_URL + link
    else:
        # Try to find link in other ways
        link = ""
    
    # Extract company
    company_elem = element.find('span', class_=re.compile(r'company|recruiter'))
    company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
    
    # Extract location
    location_elem = element.find('span', class_=re.compile(r'location|place'))
    location = location_elem.get_text(strip=True) if location_elem else "UK"
    
    # Extract date posted
    date_elem = element.find('time') or element.find('span', class_=re.compile(r'date|posted'))
    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%Y-%m-%d")
    
    # Clean and parse date
    date_str = re.sub(r'[^\d\w\s/]', '', date_str)  # Remove special chars
    date = parse_date(date_str)
    
    # Create Job instance
    job = Job(
        title=title,
        company=company,
        location=normalize_location(location),
        date=date,
        link=link,
        source="hunt_uk",
        sponsorship_confirmed=True,  # Hunt UK verifies sponsorship
        tags=extract_tags(title, "")
    )
    
    return job

if __name__ == "__main__":
    jobs = scrape_hunt_uk()
    for job in jobs[:5]:
        print(f"- {job.title} at {job.company} ({job.date})")
        print(f"  Location: {job.location}, Tags: {job.tags}")
        print()