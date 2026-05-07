#!/usr/bin/env python3
"""
LinkedIn Voyager API job scraper.
Uses authenticated cookies from Brave to access LinkedIn's embedded JSON API.
Extracts ServiceNow-specific UK roles and cross-references sponsor register.

Usage: python3 scripts/linkedin_scraper.py [--max-pages 40] [--cookie-file /tmp/li_cookies.txt]
"""

import subprocess, re, json, html as htmlmod, csv, sys, os, argparse
from pathlib import Path

# ── Config ──────────────────────────────────────────────────
SN_KEYWORDS = ['servicenow', 'snow ', 'itsm', 'csdm', 'csam', 'grcc', 'irr', 'secops', 'itom', 'hrsd', 'fsm', 'csm ']
NOISE_KEYWORDS = ['service desk', ' service desk', 'it support', 'helpdesk', 'desktop support', 'technical support', 'tech bar']
EXCLUDE_TITLE = ['salesforce', 'mac engineer', 'payroll', 'endpoint security']
COOKIE_FILE = '/tmp/li_cookies.txt'
SPONSOR_CSV = os.path.expanduser('~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv')
OUTPUT_FILE = 'docs/data/linkedin_jobs.json'
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36'

def load_sponsors():
    """Load A-rated Skilled Worker sponsors from CSV"""
    sponsors = set()
    try:
        with open(SPONSOR_CSV, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                route = row.get('Route', '')
                rating = row.get('Type & Rating', '')
                if 'skilled worker' in route.lower() and 'a rating' in rating.lower():
                    sponsors.add(row.get('Organisation Name', '').strip().lower())
    except Exception:
        pass
    return sponsors

def check_sponsor(company_name, sponsors):
    """Check if company is on the sponsor register"""
    name_lower = company_name.lower().strip()
    for s in sponsors:
        if name_lower in s or s in name_lower:
            return True
    return False

def extract_jobs_from_page(html):
    """Extract job cards from LinkedIn Voyager API embedded JSON"""
    blocks = re.findall(r'<code[^>]*>(.*?)</code>', html, re.DOTALL)
    jobs = []
    
    for raw in blocks:
        try:
            data = json.loads(htmlmod.unescape(raw))
            cards = [x for x in data.get('included', [])
                    if x.get('$type') == 'com.linkedin.voyager.dash.jobs.JobPostingCard']
            if not cards or len(cards) < 3:
                continue
            
            for c in cards:
                title = c.get('jobPostingTitle', c.get('title', {}).get('text', '')).strip()
                if not title:
                    continue
                
                # Filter for SN relevance
                title_lower = title.lower()
                if any(kw in title_lower for kw in EXCLUDE_TITLE):
                    continue
                if any(kw in title_lower for kw in NOISE_KEYWORDS):
                    continue
                if not any(kw in title_lower for kw in SN_KEYWORDS):
                    continue
                
                company = c.get('primaryDescription', {}).get('text', 'N/A')
                secondary = c.get('secondaryDescription', {})
                location = secondary.get('text', 'N/A') if isinstance(secondary, dict) else 'N/A'
                norm_urn = c.get('preDashNormalizedJobPostingUrn', '')
                jid = norm_urn.split(':')[-1] if norm_urn else 'N/A'
                
                # Other metadata
                footer = c.get('footerText', {}).get('text', '') if isinstance(c.get('footerText'), dict) else ''
                
                jobs.append({
                    'linkedin_id': jid,
                    'title': title,
                    'company': company,
                    'location': location,
                    'url': f'https://www.linkedin.com/jobs/view/{jid}' if jid != 'N/A' else '',
                    'footer': footer,
                    'source': 'linkedin'
                })
        except (json.JSONDecodeError, KeyError):
            continue
    
    return jobs

def scrape(max_pages=40, cookie_file=COOKIE_FILE):
    """Scrape LinkedIn for ServiceNow UK jobs"""
    sponsors = load_sponsors()
    all_jobs = []
    
    print(f"Loaded {len(sponsors)} sponsors")
    
    for page in range(max_pages):
        start = page * 25
        url = (f'https://www.linkedin.com/jobs/search/'
               f'?keywords=ServiceNow&location=United%20Kingdom'
               f'&geoId=101165590&f_TPR=r86400'  # last 24 hours
               f'&start={start}&count=25')
        
        try:
            result = subprocess.run([
                'curl', '-s', '-b', cookie_file,
                '-A', UA,
                '-H', 'Accept: text/html,application/xhtml+xml',
                '-H', 'Accept-Language: en-US,en;q=0.9',
                url
            ], capture_output=True, text=True, timeout=30)
            
            page_jobs = extract_jobs_from_page(result.stdout)
            
            if not page_jobs:
                # Empty page = likely end of results
                if page > 2:
                    print(f"Page {page}: empty — reached end of results")
                    break
                print(f"Page {page}: 0 jobs (skipping)")
            else:
                print(f"Page {page}: {len(page_jobs)} SN jobs")
                all_jobs.extend(page_jobs)
                
        except subprocess.TimeoutExpired:
            print(f"Page {page}: timeout")
            continue
        except Exception as e:
            print(f"Page {page}: error — {e}")
            continue
    
    # Dedupe by title + company
    seen = set()
    unique = []
    for j in all_jobs:
        key = (j['title'].lower().strip(), j['company'].lower().strip())
        if key not in seen:
            seen.add(key)
            unique.append(j)
    
    # Tag sponsorship
    for j in unique:
        j['sponsor_verified'] = check_sponsor(j['company'], sponsors)
    
    # Save
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    with open(OUTPUT_FILE, 'w') as f:
        json.dump(unique, f, indent=2)
    
    print(f"\n✓ {len(unique)} unique SN jobs saved to {OUTPUT_FILE}")
    sponsor_count = sum(1 for j in unique if j['sponsor_verified'])
    print(f"  {sponsor_count} from verified sponsors")
    
    return unique

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--max-pages', type=int, default=40)
    parser.add_argument('--cookie-file', default=COOKIE_FILE)
    args = parser.parse_args()
    
    scrape(max_pages=args.max_pages, cookie_file=args.cookie_file)
