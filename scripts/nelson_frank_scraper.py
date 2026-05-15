#!/usr/bin/env python3
"""
Nelson Frank scraper v1.1
Uses web_extract (markdown) since the page is JS-rendered.
Tags all jobs as agency-posted.

Usage: python3 scripts/nelson_frank_scraper.py
Output: docs/data/nelson_frank_jobs.json
"""

import sys, os, json, re
from datetime import datetime
from hermes_tools import web_extract

URL = 'https://www.nelsonfrank.com/servicenow-jobs-in-united-kingdom'
OUT = os.path.expanduser('~/hermes-workspace/servicenow-jobs-digest/docs/data/nelson_frank_jobs.json')
TODAY = datetime.now().strftime('%Y-%m-%d')
SCRAPED_AT = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

def main():
    print(f'Fetching Nelson Frank via web_extract...')
    result = web_extract([URL])
    
    if not result or 'results' not in result:
        print('ERROR: web_extract failed')
        return []
    
    content = result['results'][0].get('content', '')
    if not content:
        print('ERROR: no content returned')
        return []
    
    # Parse markdown job listings
    # Pattern: ### JOB TITLE\n\nlocation · salary · type
    jobs = []
    
    # Split by ### headers (job titles)
    sections = re.split(r'\n###\s+', content)
    
    for section in sections[1:]:  # skip first (preamble)
        lines = section.strip().split('\n')
        if not lines: continue
        
        title = lines[0].strip()
        
        # Skip non-ServiceNow roles
        title_lower = title.lower()
        if not any(kw in title_lower for kw in ['servicenow', 'itsm', 'csdm', 'itom', 'hrsd', 'secops']):
            continue
        
        # Skip sales/mgmt
        if any(kw in title_lower for kw in ['sales', 'account manager', 'recruiter', 'business development']):
            continue
        
        # Build URL from title slug
        slug = re.sub(r'[^a-z0-9]+', '-', title_lower).strip('-')
        
        # Extract metadata from subsequent lines
        location = 'United Kingdom'
        salary = 'Not listed'
        emp = 'permanent'
        
        full_text = ' '.join(lines[1:])
        
        # Location
        loc_match = re.search(r'(London|Manchester|Birmingham|Edinburgh|Glasgow|Bristol|Leeds|Reading|England|UK|United Kingdom|Remote|Hybrid)', full_text)
        if loc_match:
            location = loc_match.group(1)
        
        # Salary: £XX,XXX
        sal_match = re.search(r'£[\d,]+(?:\s*(?:to|-|–)\s*£[\d,]+)?(?:\s*(?:GBP|per\s+(?:annum|day|year)))?', full_text)
        if sal_match:
            salary = sal_match.group(0)
        
        if 'contract' in title_lower:
            emp = 'contract'
        
        # Role type
        role_type = 'other'
        if 'architect' in title_lower: role_type = 'architect'
        elif 'developer' in title_lower or 'engineer' in title_lower: role_type = 'developer'
        elif 'consultant' in title_lower: role_type = 'consultant'
        elif 'analyst' in title_lower: role_type = 'analyst'
        elif 'manager' in title_lower or 'lead' in title_lower: role_type = 'manager'
        
        url = f'https://www.nelsonfrank.com/servicenow-jobs-in-united-kingdom#{slug}'
        
        jobs.append({
            'title': title,
            'company': 'Nelson Frank (agency)',
            'location': location,
            'salary_display': salary,
            'date_posted': TODAY,
            'url': url,
            'source': 'Nelson Frank',
            'source_type': 'agency',
            'sn_role': True,
            'role_type': role_type,
            'remote': 'remote' if 'remote' in title_lower else ('hybrid' if 'hybrid' in title_lower else 'onsite'),
            'employment': emp,
            'sc_clearance': False,
            'grad_scheme': False,
            'link_status': 'live',
            'visa_sponsorship': 'agency_unknown',
            'sponsor_licence': False,
            'description': '',
            'scraped_at': SCRAPED_AT,
        })
    
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, 'w') as f:
        json.dump(jobs, f, indent=2, ensure_ascii=False)
    
    print(f'  {len(jobs)} ServiceNow jobs saved (agency-posted)')
    for j in jobs:
        print(f'  🏢 {j["title"][:70]}')
    
    return jobs

if __name__ == '__main__':
    main()
