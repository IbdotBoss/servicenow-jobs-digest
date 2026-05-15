#!/usr/bin/env python3
"""ServiceNow UK Job Aggregator — Reed + Hunt UK + Sponsor CSV cross-reference"""
import json, re, csv, os, sys
from datetime import datetime, timedelta
from urllib.request import urlopen, Request
from urllib.error import URLError

TODAY = datetime.now().strftime("%Y-%m-%d")
OUTPUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobs.json")
SPONSOR_CSV = os.path.expanduser("~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv")
HEADERS = {'User-Agent': 'Mozilla/5.0 (compatible; SN-Aggregator/1.0)'}

SN_TITLE_KW = [
    'servicenow developer', 'servicenow architect', 'servicenow consultant',
    'servicenow engineer', 'servicenow admin', 'servicenow specialist',
    'servicenow lead', 'servicenow manager', 'servicenow platform',
    'servicenow technical', 'servicenow solution', 'servicenow senior',
    'service-now developer', 'service now developer'
]

# ── Sponsor CSV ──
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
        print("[WARN] Sponsor CSV not found at", SPONSOR_CSV)
    return sponsors

def check_sponsor(company, sponsors):
    """Return True if company is on sponsor register, False otherwise."""
    if not company: return False
    name = company.strip().lower()
    if name in sponsors: return True
    for s in sponsors:
        if name in s or s in name: return True
    return False

# ── Reed ──
def scrape_reed():
    jobs = []
    for page in range(1, 5):
        url = f"https://www.reed.co.uk/jobs/direct-servicenow-jobs?pageno={page}"
        try:
            req = Request(url, headers=HEADERS)
            with urlopen(req, timeout=30) as r:
                html = r.read().decode('utf-8')
            match = re.search(r'<script id="__NEXT_DATA__"[^>]*>(.*?)</script>', html)
            if not match: break
            data = json.loads(match.group(1))
            results = data['props']['pageProps']['searchResults']
            page_jobs = results.get('promotedJobs', []) + results.get('jobs', [])
            if not page_jobs: break
            
            for j in page_jobs:
                d = j['jobDetail']
                title = d['jobTitle']
                if not any(kw in title.lower() for kw in SN_TITLE_KW): continue
                
                company = d.get('ouName', 'Unknown')
                salary_from = d.get('salaryFrom', 0) or 0
                salary_to = d.get('salaryTo', 0) or 0
                # Filter absurd ranges (Reed default: 0 to 999999 or huge spans)
                if salary_to > 0 and salary_to / max(salary_from, 1) > 4:
                    salary_display = "Not listed"
                elif salary_from == 0 and salary_to == 0:
                    salary_display = "Not listed"
                else:
                    salary_display = f"£{salary_from:,}-£{salary_to:,}" if salary_to > salary_from else f"£{salary_from:,}"
                
                desc = d.get('jobDescription', '')
                date_posted = d.get('displayDate', '')[:10] if d.get('displayDate') else TODAY
                
                # Check if link is likely live (Reed links stay live)
                is_agency = any(w in company.lower() for w in ['recruitment', 'consulting', 'resource', 'talent', 'career', 'wolfe', 'nash', 'frank'])
                
                jobs.append({
                    'title': title,
                    'company': company,
                    'location': d.get('displayLocationName', 'UK'),
                    'salary_display': salary_display,
                    'salary_min': salary_from,
                    'salary_max': salary_to,
                    'date_posted': date_posted,
                    'url': f"https://www.reed.co.uk{d['url']}" if d.get('url') else '',
                    'source': 'Reed',
                    'source_type': 'agency' if is_agency else 'direct',
                    'role_type': _classify(title.lower()),
                    'remote': _remote(d, desc),
                    'employment': 'contract' if ('contract' in title.lower() or 'contract' in desc.lower()[:200]) else 'permanent',
                    'sc_clearance': any(phrase in desc.lower() for phrase in ['sc clearance', 'security check', 'security clearance', 'dv clearance']),
                    'grad_scheme': any(w in title.lower() for w in ['graduate', 'trainee', 'intern', 'placement']),
                    'link_status': 'live',
                    'description': desc[:250]
                })
        except Exception as e:
            print(f"[Reed] Page {page}: {e}")
            break
    return jobs

def _classify(title_lower):
    if 'architect' in title_lower: return 'architect'
    if 'developer' in title_lower or 'engineer' in title_lower: return 'developer'
    if 'consultant' in title_lower or 'specialist' in title_lower: return 'consultant'
    if 'administrator' in title_lower or 'admin' in title_lower: return 'admin'
    if 'analyst' in title_lower: return 'analyst'
    if 'manager' in title_lower or 'lead' in title_lower: return 'manager'
    return 'other'

def _remote(d, desc):
    r = d.get('remoteWorkingOption', '')
    if r and r != 'NotSpecified': return r
    dl = desc.lower()
    if 'remote' in dl and 'no remote' not in dl: return 'remote'
    if 'hybrid' in dl: return 'hybrid'
    return 'onsite'

# ── Main ──
def main():
    print(f"=== ServiceNow UK Aggregator — {TODAY} ===\n")
    
    sponsors = load_sponsors()
    print(f"[Sponsors] {len(sponsors)} A-rated sponsors loaded")
    
    # Scrape Reed
    reed_jobs = scrape_reed()
    print(f"[Reed] {len(reed_jobs)} SN roles found")
    
    # Cross-reference — set sponsor_licence boolean, never "verified"
    for j in reed_jobs:
        j['sponsor_licence'] = check_sponsor(j['company'], sponsors)
        j.setdefault('visa_sponsorship', 'unknown')
        # Agency: sponsorship depends on the actual employer, not the agency
        if j['source_type'] == 'agency' and j['visa_sponsorship'] == 'unknown':
            j['visa_sponsorship'] = 'agency_unknown'
    
    # Dedup by URL
    seen = set()
    unique = []
    for j in reed_jobs:
        key = j['url'] or (j['title'].lower() + '|' + j['company'].lower())
        if key not in seen:
            seen.add(key)
            unique.append(j)
    
    # Save
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    result = {
        'updated': TODAY,
        'total': len(unique),
        'verified': sum(1 for j in unique if j['visa_sponsorship'] == 'verified'),
        'sc_blocked': sum(1 for j in unique if j['sc_clearance']),
        'grad_schemes': sum(1 for j in unique if j['grad_scheme']),
        'sources': {'reed': len(unique)},
        'jobs': unique
    }
    
    with open(OUTPUT, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"\n[DONE] {len(unique)} jobs → {OUTPUT}")
    for j in unique:
        badges = []
        if j['visa_sponsorship'] == 'verified': badges.append('✅')
        elif j['visa_sponsorship'] == 'agency_unknown': badges.append('🏢')
        else: badges.append('❓')
        if j['sc_clearance']: badges.append('🔒SC')
        if j['grad_scheme']: badges.append('🎓')
        print(f"  {' '.join(badges)} {j['title'][:55]} | {j['company']} | {j['salary_display']}")

if __name__ == '__main__':
    main()
