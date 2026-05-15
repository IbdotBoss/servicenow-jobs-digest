#!/usr/bin/env python3
"""Build the daily snapshot for 2026-05-10 from all source files + Hunt UK."""
import json, os, sys
from datetime import datetime

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
DAILY_DIR = os.path.join(REPO, "daily")
TODAY = "2026-05-11"

os.makedirs(DAILY_DIR, exist_ok=True)

all_jobs = []
source_counts = {}

# 1. Load JobServe
js_file = os.path.join(REPO, "jobserve_jobs.json")
if os.path.exists(js_file):
    with open(js_file) as f:
        js_jobs = json.load(f)
    for j in js_jobs:
        j['source'] = 'JobServe'
        j['source_type'] = 'aggregator'
        j.setdefault('visa_sponsorship', 'unknown')
    all_jobs.extend(js_jobs)
    source_counts['JobServe'] = len(js_jobs)
    print(f"JobServe: {len(js_jobs)} jobs")

# 2. Load LinkedIn
li_file = os.path.join(REPO, "linkedin_jobs.json")
if os.path.exists(li_file):
    with open(li_file) as f:
        li_jobs = json.load(f)
    for j in li_jobs:
        j['source'] = 'LinkedIn'
        j['source_type'] = 'direct'
        j['date_posted'] = TODAY
        j.setdefault('visa_sponsorship', 'unknown')
        j.setdefault('salary_display', 'Not listed')
        j.setdefault('role_type', 'unknown')
        j.setdefault('remote', 'unknown')
        j.setdefault('employment', 'unknown')
        j.setdefault('sc_clearance', False)
        j.setdefault('grad_scheme', False)
        j.setdefault('link_status', 'live')
        j.setdefault('description', '')
    all_jobs.extend(li_jobs)
    source_counts['LinkedIn'] = len(li_jobs)
    print(f"LinkedIn: {len(li_jobs)} jobs")

# 3. Load Reed (from jobs.json which sn_aggregator wrote)
reed_file = os.path.join(REPO, "jobs.json")
if os.path.exists(reed_file):
    with open(reed_file) as f:
        reed_data = json.load(f)
    reed_jobs = reed_data.get('jobs', [])
    for j in reed_jobs:
        j['source'] = 'Reed'
        j.setdefault('visa_sponsorship', 'agency_unknown' if j.get('source_type') == 'agency' else 'unknown')
    all_jobs.extend(reed_jobs)
    source_counts['Reed'] = len(reed_jobs)
    print(f"Reed: {len(reed_jobs)} jobs")

# 4. Hunt UK entries (from web_extract results 2026-05-11)
# Sponsor-checked companies with valid sponsor licences
# Each confirmed present on Hunt UK today or cross-referenced with career page
hunt_uk_jobs = [
    {
        "title": "Solution Architect ServiceNow",
        "company": "AVMI Kinly Ltd",
        "location": "Sunbury-upon-Thames/London/Livingston (hybrid)",
        "salary_display": "Not listed",
        "date_posted": "2026-05-02",
        "url": "https://careers.kinly.com/o/solution-architect-servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "sponsor_licence": True,
        "description": "Solution Architect ServiceNow at Kinly (AVMI). Full-time permanent. Hybrid. Still listed on Hunt UK 2026-05-11.",
        "sponsorship_scan": "sponsor_licence_true"
    },
    {
        "title": "ServiceNow Architect",
        "company": "Tata Consultancy Services UK Limited",
        "location": "London Area, UK (hybrid)",
        "salary_display": "Not listed",
        "date_posted": "2026-05-08",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-architect-at-tata-consultancy-services-4410462317",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "sponsor_licence": True,
        "description": "ServiceNow Architect at Tata Consultancy Services (TCS). London hybrid. Lead SN implementation projects. TCS is A-rated sponsor."
    },
    {
        "title": "ServiceNow Business Analyst, Associate",
        "company": "Aquiline Capital Partners Limited (BlackRock)",
        "location": "Edinburgh, UK",
        "salary_display": "Not listed",
        "date_posted": "2026-05-08",
        "url": "https://huntukvisasponsors.com/company/blackrock-investment-management-uk-limited-z0yiqsckzomk",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "analyst",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "sponsor_licence": True,
        "description": "ServiceNow Business Analyst, Associate at Aquiline Capital Partners (BlackRock affiliate). Edinburgh. CoEI team - help grow ServiceNow Centre of Excellence."
    },
    {
        "title": "ServiceNow System Admin",
        "company": "BAE Systems Plc",
        "location": "Leeds/Preston/Frimley (hybrid/flexible)",
        "salary_display": "Up to £45,000",
        "date_posted": "2026-04-30",
        "url": "https://www.baesystems.com/en/careers",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "admin",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": True,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "sc_blocked",
        "description": "ServiceNow System Admin at BAE Systems. Requires Security Clearance. Up to £45,000."
    },
]
# Agency jobs from Hunt UK (confirmed on 2026-05-11)
hunt_agency_jobs = [
    {
        "title": "ServiceNow Product Manager (Banking)",
        "company": "SThree",
        "location": "Knutsford/Manchester (hybrid)",
        "salary_display": "£70,000-£100,000",
        "date_posted": "2026-04-30",
        "url": "https://www.sthree.com/",
        "source": "Hunt UK",
        "source_type": "agency",
        "role_type": "manager",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "ServiceNow Product Manager - Banking at SThree. Grow ServiceNow centre of excellence in banking. Still listed 2026-05-11."
    },
    {
        "title": "ServiceNow Telecommunications Service Management (TSM) Architect",
        "company": "Ubique Systems UK Limited",
        "location": "London (hybrid – 3 days onsite)",
        "salary_display": "Not listed",
        "date_posted": "2026-04-29",
        "url": "https://www.ubiquesystems.com/",
        "source": "Hunt UK",
        "source_type": "agency",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "contract",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "ServiceNow TSM Architect at Ubique Systems UK. TSM, ITSM & ITOM expertise. Still listed 2026-05-11."
    },
]

all_jobs.extend(hunt_uk_jobs)
all_jobs.extend(hunt_agency_jobs)
source_counts['Hunt UK'] = len(hunt_uk_jobs) + len(hunt_agency_jobs)
print(f"Hunt UK: {len(hunt_uk_jobs) + len(hunt_agency_jobs)} jobs ({len(hunt_uk_jobs)} verified, {len(hunt_agency_jobs)} agency)")

# Count sponsorship tags
tags = {}
for j in all_jobs:
    t = j.get('visa_sponsorship', 'unknown')
    tags[t] = tags.get(t, 0) + 1

# Build daily snapshot
snapshot = {
    "updated": TODAY,
    "total": len(all_jobs),
    "verified": tags.get('verified', 0),
    "sc_blocked": tags.get('sc_blocked', 0),
    "grad_schemes": tags.get('grad_scheme', 0),
    "sources": source_counts,
    "jobs": all_jobs
}

# Save snapshot
today_file = os.path.join(DAILY_DIR, f"jobs_{TODAY}.json")
with open(today_file, 'w') as f:
    json.dump(snapshot, f, indent=2)

print(f"\n✅ Daily snapshot saved: {today_file}")
print(f"   Total: {snapshot['total']} jobs")
print(f"   Sources: {source_counts}")
print(f"   Verified: {tags.get('verified', 0)} | SC-blocked: {tags.get('sc_blocked', 0)} | Agency: {tags.get('agency_unknown', 0)} | Unknown: {tags.get('unknown', 0)}")
