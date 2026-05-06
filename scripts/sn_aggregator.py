#!/usr/bin/env python3
"""ServiceNow UK Job Aggregator — Reed + Hunt UK + Sponsor Cross-Reference"""
import json, re, csv, sys, os
from datetime import datetime
from urllib.request import urlopen, Request
from urllib.error import URLError

OUTPUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobs.json")
SPONSOR_CSV = os.path.expanduser("~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv")
TODAY = datetime.now().strftime("%Y-%m-%d")

SN_KEYWORDS = [
    'servicenow developer', 'servicenow architect', 'servicenow consultant',
    'servicenow engineer', 'servicenow admin', 'servicenow specialist',
    'servicenow lead', 'servicenow manager', 'servicenow analyst',
    'servicenow platform', 'servicenow technical', 'servicenow solution',
    'service-now developer', 'service now developer'
]

# ─────────────────── Sponsor CSV Loader ───────────────────
def load_sponsors():
    sponsors = set()
    try:
        with open(SPONSOR_CSV, 'r', encoding='utf-8-sig') as f:
            for row in csv.DictReader(f):
                org = row.get('Organisation Name', '').strip().lower()
                route = row.get('Route', '').lower()
                rating = row.get('Type & Rating', '').lower()
                if org and 'skilled worker' in route and 'a rating' in rating:
                    sponsors.add(org)
    except FileNotFoundError:
        print("[WARN] Sponsor CSV not found")
    return sponsors

def check_sponsorship(company_name, sponsors):
    """Check if company is on the sponsor register"""
    if not company_name:
        return "unknown"
    name = company_name.strip().lower()
    # Direct match
    if name in sponsors:
        return "verified"
    # Partial match (e.g. "Capgemini UK PLC" matches "capgemini")
    for s in sponsors:
        if name in s or s in name:
            return "verified"
    return "unknown"

# ─────────────────── Reed Scraper ───────────────────
def scrape_reed():
    """Scrape all Reed pages for ServiceNow jobs"""
    all_jobs = []
    headers = {'User-Agent': 'Mozilla/5.0 (compatible; ServiceNowAggregator/1.0)'}
    
    for page in range(1, 5):
        url = f"https://www.reed.co.uk/jobs/direct-servicenow-jobs?pageno={page}"
        try:
            req = Request(url, headers=headers)
            with urlopen(req, timeout=30) as resp:
                html = resp.read().decode('utf-8')
            
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
            if not match:
                break
            
            data = json.loads(match.group(1))
            results = data['props']['pageProps']['searchResults']
            page_jobs = results.get('promotedJobs', []) + results.get('jobs', [])
            
            if not page_jobs:
                break
                
            for job in page_jobs:
                d = job['jobDetail']
                title = d['jobTitle']
                title_lower = title.lower()
                
                # Only include actual ServiceNow roles
                is_sn = any(kw in title_lower for kw in SN_KEYWORDS)
                if not is_sn:
                    continue
                
                company = d.get('ouName', 'Unknown')
                location = d.get('displayLocationName', 'UK')
                county = d.get('countyLocation', '')
                salary_from = d.get('salaryFrom', 0)
                salary_to = d.get('salaryTo', 0)
                remote = d.get('remoteWorkingOption', '')
                fulltime = d.get('isFullTime', False)
                date_posted = d.get('displayDate', '')[:10] if d.get('displayDate') else TODAY
                url = f"https://www.reed.co.uk{d['url']}" if d.get('url') else ''
                desc = d.get('jobDescription', '')[:500]
                
                # Role classification
                role_type = classify_role(title_lower)
                
                # Remote tag
                remote_tag = remote if remote and remote != 'NotSpecified' else ('hybrid' if 'hybrid' in desc.lower() else 'onsite')
                
                all_jobs.append({
                    'title': title,
                    'company': company,
                    'location': location,
                    'county': county,
                    'salary_min': salary_from,
                    'salary_max': salary_to,
                    'salary_display': f"£{salary_from:,}-£{salary_to:,}" if salary_from else "Not listed",
                    'date_posted': date_posted,
                    'url': url,
                    'source': 'Reed',
                    'source_type': 'direct' if 'recruitment' not in company.lower() and 'consulting' not in company.lower() else 'agency',
                    'role_type': role_type,
                    'remote': remote_tag,
                    'employment': 'contract' if 'contract' in title_lower or 'contract' in desc.lower()[:200] else 'permanent',
                    'description': desc[:300],
                    'sc_clearance': 'sc clearance' in desc.lower() or 'security check' in desc.lower() or 'security clearance' in desc.lower(),
                    'grad_scheme': 'graduate' in title_lower or 'trainee' in title_lower or 'intern' in title_lower or 'placement' in title_lower,
                })
            
            print(f"[Reed] Page {page}: {len([j for j in page_jobs if any(kw in j['jobDetail']['jobTitle'].lower() for kw in SN_KEYWORDS)])} SN roles")
            
        except Exception as e:
            print(f"[Reed] Page {page} error: {e}")
            break
    
    return all_jobs

def classify_role(title_lower):
    if 'architect' in title_lower: return 'architect'
    if 'developer' in title_lower or 'engineer' in title_lower: return 'developer'
    if 'consultant' in title_lower or 'specialist' in title_lower: return 'consultant'
    if 'administrator' in title_lower or 'admin' in title_lower: return 'admin'
    if 'analyst' in title_lower: return 'analyst'
    if 'manager' in title_lower or 'lead' in title_lower: return 'manager'
    return 'other'

# ─────────────────── Main ───────────────────
def main():
    print(f"=== ServiceNow UK Job Aggregator — {TODAY} ===\n")
    
    # 1. Load sponsor register
    sponsors = load_sponsors()
    print(f"[Sponsors] {len(sponsors)} A-rated Skilled Worker sponsors loaded\n")
    
    # 2. Scrape Reed
    print("[Reed] Scraping...")
    jobs = scrape_reed()
    
    # 3. Cross-reference sponsorship
    for job in jobs:
        job['visa_sponsorship'] = check_sponsorship(job['company'], sponsors)
    
    # 4. Deduplicate by URL
    seen = set()
    unique = []
    for job in jobs:
        key = job['url'] or job['title'].lower() + '|' + job['company'].lower()
        if key not in seen:
            seen.add(key)
            unique.append(job)
    
    # 5. Save
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w') as f:
        json.dump({
            'updated': TODAY,
            'total': len(unique),
            'sponsored': sum(1 for j in unique if j['visa_sponsorship'] == 'verified'),
            'sources': {'reed': sum(1 for j in unique if j['source'] == 'Reed')},
            'jobs': unique
        }, f, indent=2)
    
    print(f"\n[DONE] {len(unique)} unique jobs saved to {OUTPUT}")
    print(f"  Sponsored: {sum(1 for j in unique if j['visa_sponsorship'] == 'verified')}")
    print(f"  SC Clearance: {sum(1 for j in unique if j['sc_clearance'])}")
    print(f"  Grad schemes: {sum(1 for j in unique if j['grad_scheme'])}")

if __name__ == '__main__':
    main()
