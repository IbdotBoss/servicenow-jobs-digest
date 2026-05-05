#!/usr/bin/env python3
"""
ServiceNow Jobs Scraper - All-in-One
Scrapes multiple sources and saves to JSON
"""

import requests
from bs4 import BeautifulSoup
import re
from datetime import datetime
from job_model import Job, parse_date, normalize_location, extract_tags
import json
from pathlib import Path

# Configuration
DATA_DIR = Path.home() / "hermes-workspace" / "servicenow-jobs-digest" / "docs" / "data"
JSON_FILE = DATA_DIR / "jobs.json"
DATA_DIR.mkdir(parents=True, exist_ok=True)

# Common headers
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1"
}

def scrape_hunt_uk() -> list[Job]:
    """Scrape Hunt UK Visa Sponsors"""
    jobs = []
    url = "https://huntukvisasponsors.com/job/search/?search=servicenow"
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        job_cards = soup.find_all('div', class_=re.compile(r'job-listing|job-card|job-item'))
        if not job_cards:
            job_cards = soup.find_all('article')
        
        for card in job_cards[:15]:
            try:
                job = parse_hunt_uk_job(card)
                if job:
                    jobs.append(job)
            except Exception as e:
                continue
                
    except Exception as e:
        print(f"[Hunt UK] Error: {e}")
    
    return jobs

def parse_hunt_uk_job(card) -> Job | None:
    title_elem = card.find('h2') or card.find('h3') or card.find('a', class_=re.compile(r'title|job-title'))
    if not title_elem:
        return None
    title = title_elem.get_text(strip=True)
    
    link_elem = card.find('a', href=True)
    if not link_elem:
        return None
    link = link_elem['href']
    if link.startswith('/'):
        link = "https://huntukvisasponsors.com" + link
    
    company_elem = card.find('span', class_=re.compile(r'company|recruiter|employer'))
    company = company_elem.get_text(strip=True) if company_elem else "Unknown Company"
    
    location_elem = card.find('span', class_=re.compile(r'location|place'))
    location = location_elem.get_text(strip=True) if location_elem else "UK"
    
    date_elem = card.find('time') or card.find('span', class_=re.compile(r'date|posted'))
    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%Y-%m-%d")
    date_str = re.sub(r'[^\d\w\s/]', '', date_str)
    date = parse_date(date_str)
    
    return Job(
        title=title,
        company=company,
        location=normalize_location(location),
        date=date,
        link=link,
        source="hunt_uk",
        sponsorship_confirmed=True,
        tags=extract_tags(title, "")
    )

def scrape_linkedin() -> list[Job]:
    jobs = []
    base_url = "https://www.linkedin.com/jobs"
    
    params = {
        "keywords": "ServiceNow",
        "location": "United Kingdom",
        "trk": "jobs_search_button",
        "f_TP": "1"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('li', class_=re.compile(r'job-card|job-item|base-card'))
            for card in job_cards[:10]:
                try:
                    job = parse_linkedin_job(card)
                    if job:
                        job.source = "linkedin"
                        job.sponsorship_confirmed = False
                        jobs.append(job)
                except: pass
    except: pass
    
    return jobs

def parse_linkedin_job(card) -> Job | None:
    title_elem = card.find('h2') or card.find('h3')
    if not title_elem: return None
    title = title_elem.get_text(strip=True)
    
    link_elem = card.find('a', href=True)
    if not link_elem: return None
    link = link_elem['href']
    if link and not link.startswith('http'):
        link = f"https://www.linkedin.com{link}"
    
    company_elem = card.find('span', class_=re.compile(r'company|org|business-name'))
    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
    
    location_elem = card.find('span', class_=re.compile(r'location|place'))
    location = location_elem.get_text(strip=True) if location_elem else "UK"
    
    date_elem = card.find('span', class_=re.compile(r'date|posted'))
    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%Y-%m-%d")
    date_str = re.sub(r' ago', '', date_str)
    date = parse_date(date_str)
    
    return Job(
        title=title,
        company=company,
        location=normalize_location(location),
        date=date,
        link=link,
        tags=extract_tags(title, "")
    )

def scrape_indeed() -> list[Job]:
    jobs = []
    base_url = "https://www.indeed.co.uk"
    
    params = {
        "q": "ServiceNow",
        "l": "United Kingdom",
        "sort": "date",
        "fromage": "7"
    }
    
    try:
        response = requests.get(base_url, params=params, headers=HEADERS, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            job_cards = soup.find_all('div', class_=re.compile(r'jobsearch-SerpJobCard|job_card'))
            for card in job_cards[:20]:
                try:
                    job = parse_indeed_job(card)
                    if job:
                        job.source = "indeed"
                        job.sponsorship_confirmed = False
                        jobs.append(job)
                except: pass
    except: pass
    
    return jobs

def parse_indeed_job(card) -> Job | None:
    title_elem = card.find('h2', class_=re.compile(r'title|jobTitle'))
    if not title_elem: return None
    title_elem = title_elem.find('a') or title_elem
    title = title_elem.get_text(strip=True)
    
    link_elem = card.find('a', href=True)
    if not link_elem: return None
    link = "https://www.indeed.co.uk" + link_elem['href']
    
    company_elem = card.find('span', class_=re.compile(r'company|companyName'))
    company = company_elem.get_text(strip=True) if company_elem else "Unknown"
    
    location_elem = card.find('span', class_=re.compile(r'location|workLocation'))
    location = location_elem.get_text(strip=True) if location_elem else "UK"
    
    date_elem = card.find('span', class_=re.compile(r'date|jobAge'))
    date_str = date_elem.get_text(strip=True) if date_elem else datetime.now().strftime("%Y-%m-%d")
    date = parse_date(date_str)
    
    return Job(
        title=title,
        company=company,
        location=normalize_location(location),
        date=date,
        link=link,
        tags=extract_tags(title, "")
    )

def main():
    print("="*60)
    print("SERVICE NOW JOBS SCRAPER")
    print("="*60)
    
    all_jobs = []
    
    # Hunt UK
    print("\n1. Scraping Hunt UK...")
    hunt_jobs = scrape_hunt_uk()
    all_jobs.extend(hunt_jobs)
    print(f"   Found {len(hunt_jobs)} jobs")
    
    # LinkedIn
    print("\n2. Scraping LinkedIn...")
    linkedin_jobs = scrape_linkedin()
    all_jobs.extend(linkedin_jobs)
    print(f"   Found {len(linkedin_jobs)} jobs")
    
    # Indeed
    print("\n3. Scraping Indeed...")
    indeed_jobs = scrape_indeed()
    all_jobs.extend(indeed_jobs)
    print(f"   Found {len(indeed_jobs)} jobs")
    
    # Deduplicate
    seen = set()
    unique_jobs = []
    for job in all_jobs:
        if job.link and job.link not in seen:
            seen.add(job.link)
            unique_jobs.append(job)
    
    print(f"\nTotal unique jobs: {len(unique_jobs)}")
    
    # Save JSON
    with open(JSON_FILE, 'w') as f:
        json.dump([j.to_dict() for j in unique_jobs], f, indent=2)
    
    print(f"\n✅ Saved to {JSON_FILE}")
    print("="*60)

if __name__ == "__main__":
    main()