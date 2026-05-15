#!/usr/bin/env python3
"""
ServiceNow Careers RSS scraper v1.0
Parses the official ServiceNow careers RSS XML feed for UK-based technical roles.
ServiceNow is on the A-rated Skilled Worker sponsor register — every job is a guaranteed sponsor.

Source: https://careers.servicenow.com/jobs/xml/?rss=true
Output: docs/data/servicenow_careers_jobs.json

Usage: python3 scripts/servicenow_careers_scraper.py
"""

import xml.etree.ElementTree as ET
import urllib.request
import json, os, re, csv
from datetime import datetime

RSS_URL = 'https://careers.servicenow.com/jobs/xml/?rss=true'
OUT = os.path.expanduser('~/hermes-workspace/servicenow-jobs-digest/docs/data/servicenow_careers_jobs.json')
SPONSOR_CSV = os.path.expanduser('~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv')
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36'
TODAY = datetime.now().strftime('%Y-%m-%d')
SCRAPED_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

# Roles to exclude — not technical ServiceNow platform roles
EXCLUDE_TITLE_KW = [
    'account exec', 'sales', 'customer success', 'marketing',
    'recruiter', 'hr ', 'people ', 'facilities', 'office manager',
    'executive assistant', 'finance', 'legal', 'compliance officer',
    'customer advocate', 'president', 'strategy director',
    'program manager', 'program director', 'business strategy',
]

def classify_role(title_lower):
    """Classify job role type from title."""
    if 'architect' in title_lower: return 'architect'
    if 'developer' in title_lower or 'engineer' in title_lower: return 'developer'
    if 'consultant' in title_lower or 'specialist' in title_lower: return 'consultant'
    if 'administrator' in title_lower or 'admin' in title_lower: return 'admin'
    if 'analyst' in title_lower: return 'analyst'
    if 'manager' in title_lower or 'lead' in title_lower: return 'manager'
    return 'other'

def scrape():
    print(f'Fetching ServiceNow Careers RSS...')
    
    req = urllib.request.Request(RSS_URL, headers={'User-Agent': UA})
    resp = urllib.request.urlopen(req, timeout=30)
    tree = ET.parse(resp)
    root = tree.getroot()
    
    jobs = []
    excluded = 0
    
    for job_el in root.findall('job'):
        country = (job_el.findtext('country') or '').strip()
        title = (job_el.findtext('title') or '').strip()
        city = (job_el.findtext('city') or '').strip()
        url = (job_el.findtext('url') or '').strip()
        description = (job_el.findtext('description') or '').strip()
        date_str = (job_el.findtext('date') or '').strip()
        jobtype = (job_el.findtext('jobtype') or '').strip()
        
        # UK only
        if country != 'United Kingdom':
            continue
        
        # Exclude non-technical
        title_lower = title.lower()
        if any(kw in title_lower for kw in EXCLUDE_TITLE_KW):
            excluded += 1
            continue
        
        # Parse date: "Fri, 15 May 2026 11:08:12 GMT" → YYYY-MM-DD HH:MM:SS
        date_posted = TODAY
        try:
            dt = datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S %Z')
            date_posted = dt.strftime('%Y-%m-%d %H:%M:%S')
        except:
            pass
        
        # Build location string
        location = city
        if country and country != city:
            if location:
                location += ', ' + country
            else:
                location = country
        
        # Strip HTML from description for display
        desc_clean = re.sub(r'<[^>]+>', ' ', description)
        desc_clean = re.sub(r'\s+', ' ', desc_clean).strip()[:300]
        
        # Determine remote status
        remote = 'hybrid'
        if 'remote' in title_lower:
            remote = 'remote'
        elif 'on-site' in title_lower or 'onsite' in title_lower:
            remote = 'onsite'
        
        # SC/DV check
        sc = any(p in title_lower for p in [
            'sc cleared', 'sc-cleared', 'security clearance', 'security cleared',
            'dv cleared', 'dv-cleared', 'developed vetting',
        ])
        
        jobs.append({
            'title': title,
            'company': 'ServiceNow',
            'location': location,
            'salary_display': 'Not listed',
            'date_posted': date_posted,
            'url': url,
            'source': 'ServiceNow Careers',
            'source_type': 'employer',
            'sn_role': True,
            'role_type': classify_role(title_lower),
            'remote': remote,
            'employment': 'permanent' if 'full-time' in jobtype.lower() else 'contract',
            'sc_clearance': sc,
            'grad_scheme': False,
            'link_status': 'live',
            'visa_sponsorship': 'unknown',
            'sponsor_licence': True,  # ServiceNow IS on the register
            'description': desc_clean if desc_clean else '',
            'scraped_at': SCRAPED_AT,
        })
    
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    print(f'  {len(jobs)} UK technical roles saved ({excluded} non-technical excluded)')
    for j in jobs[:8]:
        sc_badge = '🔒' if j.get('sc_clearance') else '  '
        print(f'  {sc_badge} 🟣 {j["title"][:65]}')
        print(f'       {j["location"]} | {j["date_posted"]}')
    
    return jobs

if __name__ == '__main__':
    scrape()
