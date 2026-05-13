#!/usr/bin/env python3
"""Build daily snapshot for 2026-05-13 from all source files + Hunt UK."""
import json, os
from datetime import datetime

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
DAILY_DIR = os.path.join(REPO, "daily")
TODAY = "2026-05-13"

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

# 2. Load LinkedIn (may be empty if no cookies)
li_file = os.path.join(REPO, "linkedin_jobs.json")
if os.path.exists(li_file):
    with open(li_file) as f:
        li_jobs = json.load(f)
    if isinstance(li_jobs, list) and len(li_jobs) > 0:
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

# 4. Hunt UK entries with resolved LinkedIn URLs
hunt_uk_jobs = [
    {
        "title": "ServiceNow Telecommunications Service Management (TSM) Architect",
        "company": "UBIQUE SYSTEMS UK LIMITED",
        "location": "London Area (hybrid)",
        "salary_display": "Not listed",
        "date_posted": "2026-05-08",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-telecommunications-service-management-tsm-architect-at-ubique-systems-4411863814",
        "fallback_url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "contract",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "Designs and governs end-to-end solutions within the ServiceNow TSM module, aligning with ITOM, ITIL, and CMDB/CSDM standards. Contract role."
    },
    {
        "title": "ServiceNow Architect (TSM)",
        "company": "UBIQUE SYSTEMS UK LIMITED",
        "location": "London Area (hybrid, 3 days/week)",
        "salary_display": "Not listed",
        "date_posted": "2026-05-08",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-architect-tsm-at-ubique-systems-4406073929",
        "fallback_url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "contract",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "ServiceNow Architect with TSM expertise. 6-month contract, extendable, Outside IR35. Hybrid 3 days/week in London."
    },
    {
        "title": "ServiceNow Architect",
        "company": "TATA CONSULTANCY SERVICES UK LIMITED",
        "location": "London (Hybrid)",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-architect-at-tata-consultancy-services-4410462317",
        "fallback_url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "ServiceNow Architect at TCS. Permanent, hybrid in London. Contact UKI.recruitment@tcs.com."
    },
    {
        "title": "Solution Architect ServiceNow",
        "company": "AVMI Kinly Ltd",
        "location": "Sunbury-upon-Thames/London/Livingston (hybrid, 1 day/week onsite)",
        "salary_display": "Excellent salary + bonus + benefits",
        "date_posted": "2026-05-07",
        "url": "https://uk.linkedin.com/jobs/view/solution-architect-servicenow-at-kinly-4413299904",
        "fallback_url": "https://careers.kinly.com/o/solution-architect-servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "Solution Architect ServiceNow at Kinly. Hybrid - 1 day/week onsite. Excellent salary, bonus and benefits. No recruitment agencies."
    },
    {
        "title": "Software Asset Management & CMDB Lead (ServiceNow)",
        "company": "METHODS BUSINESS AND DIGITAL TECHNOLOGY LIMITED",
        "location": "London, England",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://uk.linkedin.com/jobs/view/software-asset-management-cmdb-lead-servicenow-at-methods-4409279637",
        "fallback_url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "manager",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "Software Asset Management & CMDB Lead to support a major Zero Trust programme. Central government/public sector focus."
    },
    {
        "title": "ServiceNow Business Analyst, Associate",
        "company": "Aquiline Capital Partners Limited",
        "location": "Edinburgh, Scotland",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "fallback_url": "",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "analyst",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "ServiceNow Business Analyst within the CoEI team at Aquiline Capital Partners. Work with business collaborators and technical teams."
    },
    {
        "title": "ServiceNow Engineer",
        "company": "Barclays Execution Services Limited",
        "location": "Knutsford, England",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://uk.linkedin.com/jobs/view/senior-servicenow-engineer-at-barclays-4406001068",
        "fallback_url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "developer",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "ServiceNow Engineer at Barclays. Design, code and deliver scalable, high-impact solutions on the ServiceNow platform."
    },
    {
        "title": "HR Transformation Consultant / Senior Consultant (ServiceNow HRSD)",
        "company": "GAUBERT'S BROTHERS LIMITED (via Capgemini Invent)",
        "location": "Glasgow, Scotland",
        "salary_display": "Not listed",
        "date_posted": "2026-05-07",
        "url": "https://jm.linkedin.com/jobs/view/hr-transformation-consultant-senior-consultant-servicenow-hrsd-at-capgemini-4372182142",
        "fallback_url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "agency",
        "role_type": "consultant",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "HR Transformation Consultant/Senior Consultant (ServiceNow HRSD) via Capgemini Invent based in Glasgow. Strategic consulting."
    },
    {
        "title": "ServiceNow Product Manager",
        "company": "SThree (banking client)",
        "location": "Knutsford or Manchester (hybrid, 2 days/week)",
        "salary_display": "£70,000-£100,000",
        "date_posted": "2026-05-07",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-product-manager-at-huxley-4410821268",
        "fallback_url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "agency",
        "role_type": "manager",
        "remote": "hybrid",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "Product Manager - ServiceNow at a banking client via SThree (Huxley). £70k-£100k. Hybrid Knutsford/Manchester."
    },
    {
        "title": "ServiceNow GTM / Solutions Sales Lead",
        "company": "HCL Technologies UK Limited",
        "location": "London Area",
        "salary_display": "Not listed",
        "date_posted": "2026-05-06",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-gtm-solutions-sales-lead-at-hcltech-4409790542",
        "fallback_url": "https://huntukvisasponsors.com/jobs?q=servicenow",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "other",
        "remote": "onsite",
        "employment": "permanent",
        "sc_clearance": False,
        "grad_scheme": False,
        "link_status": "live",
        "description": "ServiceNow GTM / Solutions Sales Lead at HCLTech. Drive joint account planning, QBRs, and partner relationships in the ServiceNow ecosystem."
    },
]

for j in hunt_uk_jobs:
    j.setdefault('visa_sponsorship', 'unknown')
all_jobs.extend(hunt_uk_jobs)
source_counts['Hunt UK'] = len(hunt_uk_jobs)
print(f"Hunt UK: {len(hunt_uk_jobs)} jobs")

# Dedup by (title, company) within this snapshot
seen = set()
unique_jobs = []
for j in all_jobs:
    title = j.get('title', '').lower().strip()
    company = j.get('company', '').lower().strip()
    key = f"{title}|{company}"
    if key not in seen:
        seen.add(key)
        unique_jobs.append(j)

print(f"\nTotal unique: {len(unique_jobs)} (deduped from {len(all_jobs)})")
print(f"Sources: {source_counts}")

# Save daily snapshot
snapshot = {
    'updated': TODAY,
    'total': len(unique_jobs),
    'sources': source_counts,
    'jobs': unique_jobs
}

snapshot_path = os.path.join(DAILY_DIR, f"jobs_{TODAY}.json")
with open(snapshot_path, 'w') as f:
    json.dump(snapshot, f, indent=2, ensure_ascii=False)

print(f"\n✅ Snapshot saved: {snapshot_path}")
print(f"   {len(unique_jobs)} jobs from {len(source_counts)} sources")
