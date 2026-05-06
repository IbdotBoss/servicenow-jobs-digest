#!/usr/bin/env python3
"""Merge Reed scraped data with Hunt UK + LinkedIn + Grad listings — produce final jobs.json"""
import json, os, csv
from datetime import datetime, timedelta

TODAY = datetime.now().strftime("%Y-%m-%d")
BASE = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest")
INPUT = os.path.join(BASE, "docs/data/jobs.json")  # from sn_aggregator.py
OUTPUT = os.path.join(BASE, "docs/data/jobs.json")
SPONSOR_CSV = os.path.expanduser("~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv")

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
    except: pass
    return sponsors

def check(company, sponsors):
    if not company: return "unknown"
    name = company.strip().lower()
    if name in sponsors: return "verified"
    for s in sponsors:
        if name in s or s in name: return "verified"
    return "unknown"

def main():
    sponsors = load_sponsors()
    
    # Load Reed jobs (or start fresh)
    reed_jobs = []
    if os.path.exists(INPUT):
        try:
            with open(INPUT) as f:
                existing = json.load(f)
                reed_jobs = existing.get('jobs', [])
        except: pass
    
    # ── Hunt UK manual additions (from web_extract) ──
    hunt_jobs = [
        {
            "title": "ServiceNow Developer, AVP",
            "company": "State Street Bank",
            "location": "London",
            "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
            "date_posted": "2026-04-22",
            "url": "https://huntukvisasponsors.com/job/servicenow-developer-at-state-street-bank-and-trust-company-4b6mxtzqt4t",
            "fallback_url": "https://statestreet.wd5.myworkdayjobs.com/Global/search?q=servicenow",
            "source": "Hunt UK", "source_type": "direct",
            "role_type": "developer", "remote": "hybrid", "employment": "permanent",
            "sc_clearance": True, "grad_scheme": False,
            "link_status": "expired",
            "description": "Support and implement ServiceNow solutions. Design, build, and customize platform applications. Member of a geographically distributed team."
        },
        {
            "title": "ServiceNow Senior Developer (11m Contract)",
            "company": "Clifford Chance",
            "location": "UK-wide",
            "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
            "date_posted": "2026-04-22",
            "url": "https://huntukvisasponsors.com/job/servicenow-senior-developer-11-months-contract-at-gauberts-brothers-limited-ru0et0agp9ly",
            "fallback_url": "https://cliffordchance.wd3.myworkdayjobs.com/Careers/search?q=servicenow",
            "source": "Hunt UK", "source_type": "direct",
            "role_type": "developer", "remote": "hybrid", "employment": "contract",
            "sc_clearance": False, "grad_scheme": False,
            "link_status": "expired",
            "description": "Maintenance, configuration and development of the Firm's ITSM tool, ServiceNow. Working within an agreed governance model."
        },
        {
            "title": "ServiceNow Developer",
            "company": "Capgemini UK",
            "location": "London",
            "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
            "date_posted": "2026-04-14",
            "url": "https://huntukvisasponsors.com/job/servicenow-developer-at-capgemini-uk-plc-dvetgmhjcls",
            "fallback_url": "https://www.capgemini.com/gb-en/careers/",
            "source": "Hunt UK", "source_type": "direct",
            "role_type": "developer", "remote": "hybrid", "employment": "permanent",
            "sc_clearance": True, "grad_scheme": False,
            "link_status": "expired",
            "description": "Design, develop, and maintain ServiceNow applications. Virtual Agent, RPA flows. JavaScript, ITSM, ITOM. SC clearance required — 5yr UK residency."
        },
        {
            "title": "Senior ServiceNow Developer / Architect",
            "company": "IBM UK",
            "location": "UK-wide",
            "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
            "date_posted": "2026-04-22",
            "url": "https://huntukvisasponsors.com/job/senior-servicenow-developer-architect-at-ibm-uk-ltd-q6eu3tyaitdl",
            "fallback_url": "https://www.ibm.com/careers/uk-en/search?filters=primary_skill:ServiceNow",
            "source": "Hunt UK", "source_type": "direct",
            "role_type": "architect", "remote": "hybrid", "employment": "permanent",
            "sc_clearance": False, "grad_scheme": False,
            "link_status": "expired",
            "description": "IBM Consulting. Long-term client relationships and close collaboration worldwide. Hybrid cloud and AI journeys."
        },
    ]
    
    # ── LinkedIn ──
    li_jobs = [
        {
            "title": "ServiceNow Developer",
            "company": "Akoni Technologies",
            "location": "Reading, Berkshire",
            "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
            "date_posted": "2026-01-06",
            "url": "https://uk.linkedin.com/jobs/view/servicenow-developer-at-akoni-technologies-3830988858",
            "source": "LinkedIn", "source_type": "direct",
            "role_type": "developer", "remote": "onsite", "employment": "permanent",
            "sc_clearance": False, "grad_scheme": False,
            "link_status": "stale",
            "description": "Visa Sponsorship (Skilled Worker Visa) can be provided. Hands-on experience designing and developing ServiceNow solutions."
        },
    ]
    
    # ── Grad schemes ──
    grad_jobs = [
        {
            "title": "Graduate ServiceNow Technical Consultant 2026",
            "company": "Capgemini",
            "location": "London",
            "salary_display": "£30,000", "salary_min": 30000, "salary_max": 30000,
            "date_posted": "2026-03-15",
            "url": "https://www.capgemini.com/gb-en/careers/",
            "source": "Capgemini Careers", "source_type": "direct",
            "role_type": "consultant", "remote": "hybrid", "employment": "permanent",
            "sc_clearance": False, "grad_scheme": True,
            "link_status": "live",
            "description": "Sep 2026 start. £30,000 salary. Training & development. ServiceNow platform solutions for clients across industries."
        },
    ]
    
    # ── Combine ──
    all_jobs = reed_jobs.copy()
    
    for hunt in hunt_jobs:
        hunt['visa_sponsorship'] = 'verified' if not hunt['sc_clearance'] else 'sc_blocked'
        # Don't add if already in Reed
        key = hunt['title'].lower() + '|' + hunt['company'].lower()
        if not any(j['title'].lower() + '|' + j['company'].lower() == key for j in all_jobs):
            all_jobs.append(hunt)
    
    for li in li_jobs:
        li['visa_sponsorship'] = check(li['company'], sponsors)
        key = li['title'].lower() + '|' + li['company'].lower()
        if not any(j['title'].lower() + '|' + j['company'].lower() == key for j in all_jobs):
            all_jobs.append(li)
    
    for grad in grad_jobs:
        grad['visa_sponsorship'] = check(grad['company'], sponsors)
        key = grad['title'].lower() + '|' + grad['company'].lower()
        if not any(j['title'].lower() + '|' + j['company'].lower() == key for j in all_jobs):
            all_jobs.append(grad)
    
    # Dedup
    seen = set()
    unique = []
    for j in all_jobs:
        k = j.get('url', '') or (j['title'].lower() + '|' + j['company'].lower())
        if k not in seen:
            seen.add(k)
            unique.append(j)
    
    # Stats
    result = {
        'updated': TODAY,
        'total': len(unique),
        'verified': sum(1 for j in unique if j.get('visa_sponsorship') == 'verified'),
        'sc_blocked': sum(1 for j in unique if j.get('sc_clearance')),
        'grad_schemes': sum(1 for j in unique if j.get('grad_scheme')),
        'live_links': sum(1 for j in unique if j.get('link_status') == 'live'),
        'sources': {
            'reed': sum(1 for j in unique if j.get('source') == 'Reed'),
            'hunt_uk': sum(1 for j in unique if j.get('source') == 'Hunt UK'),
            'linkedin': sum(1 for j in unique if j.get('source') == 'LinkedIn'),
            'other': sum(1 for j in unique if j.get('source') not in ['Reed', 'Hunt UK', 'LinkedIn']),
        },
        'jobs': unique
    }
    
    os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
    with open(OUTPUT, 'w') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
    
    print(f"Saved {len(unique)} jobs → {OUTPUT}")
    for j in unique:
        sp = j.get('visa_sponsorship', 'unknown')
        print(f"  [{sp}] {j['title'][:50]} | {j['company']} | {j.get('link_status','?')} | {j.get('source','?')}")

if __name__ == '__main__':
    main()
