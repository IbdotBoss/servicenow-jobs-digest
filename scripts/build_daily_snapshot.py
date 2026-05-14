#!/usr/bin/env python3
"""Build daily snapshot from all 4 sources + Hunt UK with resolved LinkedIn URLs."""
import json, os
from datetime import datetime

TODAY = "2026-05-14"
REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
DAILY_DIR = os.path.join(REPO, "daily")

os.makedirs(DAILY_DIR, exist_ok=True)

all_jobs = []
source_counts = {}

# 1. JobServe
js_file = os.path.join(REPO, "jobserve_jobs.json")
if os.path.exists(js_file):
    with open(js_file) as f:
        js_jobs = json.load(f)
    for j in js_jobs:
        j['source'] = 'JobServe'
        j['source_type'] = 'aggregator'
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
    all_jobs.extend(js_jobs)
    source_counts['JobServe'] = len(js_jobs)
    print(f"JobServe: {len(js_jobs)} jobs")

# 2. LinkedIn
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

# 3. Reed
reed_file = os.path.join(REPO, "jobs.json")
if os.path.exists(reed_file):
    with open(reed_file) as f:
        reed_data = json.load(f)
    reed_jobs = reed_data.get('jobs', [])
    for j in reed_jobs:
        j['source'] = 'Reed'
        j['source_type'] = 'agency' if j.get('source_type') == 'agency' else 'direct'
        j.setdefault('visa_sponsorship', 'agency_unknown' if j.get('source_type') == 'agency' else 'unknown')
        j.setdefault('sc_clearance', False)
        j.setdefault('grad_scheme', False)
        j.setdefault('link_status', 'live')
    all_jobs.extend(reed_jobs)
    source_counts['Reed'] = len(reed_jobs)
    print(f"Reed: {len(reed_jobs)} jobs")

# 4. Hunt UK (from web_extract + web_search results)
# These are all from licensed sponsors on the register
# visa_sponsorship set to 'unknown' — scan_sponsorship.py will set sponsor_licence boolean
hunt_uk_jobs = [
    {
        "title": "ServiceNow Telecommunications Service Management (TSM) Architect",
        "company": "Ubique Systems UK Limited",
        "location": "London Area, United Kingdom",
        "salary_display": "Not listed",
        "date_posted": "2026-05-08",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-architect-at-ubique-systems-4411866930",
        "source": "Hunt UK",
        "source_type": "agency",
        "role_type": "architect",
        "remote": "onsite",
        "employment": "contract",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "description": "ServiceNow TSM Architect at Ubique Systems. Contract. London. Design and govern end-to-end solutions within ServiceNow TSM module."
    },
    {
        "title": "ServiceNow Architect (TSM)",
        "company": "Ubique Systems UK Limited",
        "location": "London, UK (Hybrid – 3 days onsite)",
        "salary_display": "Not listed",
        "date_posted": "2026-05-08",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-architect-tsm-at-ubique-systems-4406073929",
        "source": "Hunt UK",
        "source_type": "agency",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "contract",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "description": "ServiceNow Architect TSM at Ubique Systems. 6 months extendable, Outside IR35. London hybrid."
    },
    {
        "title": "ServiceNow Architect",
        "company": "Tata Consultancy Services UK Limited",
        "location": "London, UK (Hybrid)",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
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
        "description": "ServiceNow Architect at TCS. London hybrid. Permanent. Expand skills in ServiceNow Architecture."
    },
    {
        "title": "Solution Architect ServiceNow",
        "company": "AVMI Kinly Ltd",
        "location": "Sunbury-upon-Thames, London, or Livingston (hybrid)",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://careers.kinly.com/l/pl/o/solution-architect-servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "description": "Solution Architect ServiceNow at Kinly. Permanent. Hybrid. Focus on ServiceNow CSM. No recruitment agencies."
    },
    {
        "title": "Software Asset Management & CMDB Lead (ServiceNow)",
        "company": "Methods Business and Digital Technology Limited",
        "location": "London, England",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "manager",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "description": "SAM & CMDB Lead (ServiceNow) at Methods. London. Government sector. UK public sector transformation."
    },
    {
        "title": "ServiceNow Business Analyst, Associate",
        "company": "Aquiline Capital Partners Limited",
        "location": "Edinburgh, Scotland",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "analyst",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "description": "ServiceNow Business Analyst, Associate at Aquiline Capital Partners. Edinburgh. ServiceNow CoEI team."
    },
    {
        "title": "ServiceNow Engineer",
        "company": "Barclays Execution Services Limited",
        "location": "Knutsford, England",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://uk.linkedin.com/jobs/view/senior-servicenow-engineer-at-barclays-4406001068",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "developer",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "description": "ServiceNow Engineer at Barclays. Knutsford. Design, develop, and improve software using engineering methodologies."
    },
    {
        "title": "HR Transformation Consultant / Senior Consultant (ServiceNow HRSD)",
        "company": "Capgemini Invent (Gaubert's Brothers Limited)",
        "location": "Glasgow, Scotland",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://jm.linkedin.com/jobs/view/hr-transformation-consultant-senior-consultant-servicenow-hrsd-at-capgemini-4372182142",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "consultant",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "description": "HR Transformation Consultant/Senior Consultant (ServiceNow HRSD) at Capgemini Invent. Glasgow. Permanent."
    },
    {
        "title": "ServiceNow Product Manager (Banking)",
        "company": "SThree",
        "location": "Knutsford or Manchester (2 days/week office)",
        "salary_display": "£70,000-£100,000",
        "date_posted": "2026-05-07",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-product-manager-bank-at-huxley-4407395761",
        "source": "Hunt UK",
        "source_type": "agency",
        "role_type": "manager",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "description": "ServiceNow Product Manager - Banking at SThree. £70k-£100k. Knutsford/Manchester. Own ServiceNow product within Banking CoE."
    },
    {
        "title": "ServiceNow GTM / Solutions Sales Lead",
        "company": "HCL Technologies UK Limited",
        "location": "London Area",
        "salary_display": "Not listed",
        "date_posted": "2026-05-06",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-gtm-solutions-sales-lead-at-hcltech-4409790542",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "other",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "visa_sponsorship": "unknown",
        "description": "ServiceNow GTM / Solutions Sales Lead at HCLTech. London. Drive joint account planning and ServiceNow partnership."
    },
]
all_jobs.extend(hunt_uk_jobs)
source_counts['Hunt UK'] = len(hunt_uk_jobs)
print(f"Hunt UK: {len(hunt_uk_jobs)} jobs")

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
