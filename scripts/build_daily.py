#!/usr/bin/env python3
"""Build the daily snapshot for 2026-05-10 from all source files + Hunt UK."""
import json, os, sys
from datetime import datetime

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
DAILY_DIR = os.path.join(REPO, "daily")
TODAY = "2026-05-10"

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

# 4. Hunt UK entries (from web_extract results)
# Sponsor-checked companies with valid sponsor licences
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
        "visa_sponsorship": "verified",
        "description": "Solution Architect ServiceNow at Kinly (AVMI). Full-time permanent. Hybrid.",
        "sponsorship_scan": "verified_by_register_no_sc"
    },
    {
        "title": "ServiceNow PreSales Architect",
        "company": "Solution17 Ltd",
        "location": "London",
        "salary_display": "Not listed",
        "date_posted": "2026-05-01",
        "url": "https://solution17.com/careers/",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "verified",
        "description": "ServiceNow PreSales Architect at Solution17 Ltd. Client-facing presales supporting ESM growth."
    },
    {
        "title": "ServiceNow Engineer",
        "company": "Freshfields Service Company",
        "location": "Manchester Area, UK",
        "salary_display": "Not listed",
        "date_posted": "2026-04-30",
        "url": "https://www.freshfields.com/en-gb/careers/",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "engineer",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "verified",
        "description": "ServiceNow Engineer at Freshfields. Shape, enhance and support a mature ServiceNow platform."
    },
    {
        "title": "ServiceNow Technical Lead – Insurance/FSO",
        "company": "CSC Computer Sciences Limited (DXC Technology)",
        "location": "United Kingdom (hybrid/flexible)",
        "salary_display": "Not listed",
        "date_posted": "2026-04-30",
        "url": "https://careers.dxc.com/",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "lead",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "verified",
        "description": "ServiceNow Technical Lead at DXC Technology. Lead insurance workflow solutions on ServiceNow FSO."
    },
    {
        "title": "ServiceNow Services Sales Specialist",
        "company": "INETUM DIGITAL SERVICES UK LIMITED",
        "location": "London Area, UK",
        "salary_display": "Not listed",
        "date_posted": "2026-04-30",
        "url": "https://www.inetum.com/en/careers",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "sales",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "verified",
        "description": "ServiceNow Services Sales Specialist at Inetum. Building new client base across Europe."
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
# Agency jobs from Hunt UK (SThree, Harvey Nash, X4 Group, Ubique)
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
        "description": "ServiceNow Product Manager - Banking at SThree. Grow ServiceNow centre of excellence in banking."
    },
    {
        "title": "CMDB Specialist (ServiceNow)",
        "company": "Harvey Nash Limited",
        "location": "United Kingdom (Remote)",
        "salary_display": "Not listed",
        "date_posted": "2026-04-30",
        "url": "https://www.harveynash.com/",
        "source": "Hunt UK",
        "source_type": "agency",
        "role_type": "specialist",
        "remote": "remote",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "CMDB Specialist (ServiceNow) at Harvey Nash. Global manufacturing org, 15M+ CIs, 300k employees."
    },
    {
        "title": "ServiceNow Architect (TSM)",
        "company": "X4 Group Ltd",
        "location": "London (hybrid – 3 days/week)",
        "salary_display": "£650/day (Outside IR35)",
        "date_posted": "2026-04-29",
        "url": "https://www.x4group.com/",
        "source": "Hunt UK",
        "source_type": "agency",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "contract",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "ServiceNow Architect (TSM) at X4 Group. 6 months extendable contract. £650/day Outside IR35."
    },
    {
        "title": "ServiceNow Architect – TSM",
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
        "description": "ServiceNow Architect (TSM) at Ubique Systems UK. TSM, ITSM & ITOM expertise. Telecom domain."
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
