#!/usr/bin/env python3
"""Add missed jobs from Stage's links"""
import json, os
TODAY = "2026-05-06"
OUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobs.json")

with open(OUT) as f:
    data = json.load(f)

# FIX: Replace expired IBM job with FRESH Hunt UK listing
for j in data['jobs']:
    if j['company'] == 'IBM UK' and j['source'] == 'Hunt UK' and j['link_status'] == 'expired':
        j['url'] = 'https://huntukvisasponsors.com/job/senior-servicenow-developer-architect-at-ibm-pbmqjkzfpkm'
        j['date_posted'] = '2026-04-13'
        j['location'] = 'London'
        j['link_status'] = 'live'
        j['description'] = 'Lead ServiceNow implementation projects. Effort estimation, planning, architectural analysis. API integration, cloud platforms. IBM Consulting — verified A-rated sponsor.'

# NEW: ServiceNow SIR Engineer — Knutsford (Barclays), posted YESTERDAY
new = [
    {
        "title": "ServiceNow SIR Engineer",
        "company": "Barclays via eTeam",
        "location": "Knutsford, Cheshire",
        "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
        "date_posted": "2026-05-05",
        "url": "https://www.computerjobs.com/gb/en/search-jobs-in-Knutsford,-Cheshire,-United-Kingdom/SERVICENOW-SIR-ENGINEER-3B67B1DD324FA16BF3/",
        "source": "ComputerJobs", "source_type": "agency",
        "role_type": "developer", "remote": "hybrid", "employment": "contract",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "SIR (Security Incident Response) implementation. Knutsford = Barclays tech centre. Hybrid 60% office. Contract to 30/11/2026. eTeam agency — Barclays holds A-rated sponsor licence. Verify sponsorship."
    },
    {
        "title": "ServiceNow Architect (Telecoms TSM)",
        "company": "Syntax Consultancy (agency)",
        "location": "Central London",
        "salary_display": "£600/day", "salary_min": 0, "salary_max": 0,
        "date_posted": "2026-04-29",
        "url": "https://www.computerjobs.com/gb/en/search-jobs-in-Central-London,-London,-United-Kingdom/SERVICENOW-ARCHITECT-800E1577399731715F/",
        "source": "ComputerJobs", "source_type": "agency",
        "role_type": "architect", "remote": "hybrid", "employment": "contract",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "Telecoms Service Management (TSM). 6-month contract, £600/day Outside IR35. Hybrid 3 days London office. Start May/June 2026. Syntax agency — verify sponsorship with employer."
    },
]

seen = {j.get('url','') for j in data['jobs']}
for nj in new:
    if nj['url'] not in seen:
        data['jobs'].append(nj)
        seen.add(nj['url'])

data['total'] = len(data['jobs'])
data['updated'] = TODAY
data['verified'] = sum(1 for j in data['jobs'] if j['visa_sponsorship'] == 'verified')
data['live_links'] = sum(1 for j in data['jobs'] if j['link_status'] == 'live')

srcs = {}
for j in data['jobs']:
    s = j.get('source','?')
    srcs[s] = srcs.get(s, 0) + 1
data['sources'] = srcs

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"SAVED {len(data['jobs'])} jobs from {len(srcs)} sources")
for j in data['jobs']:
    fr = '🆕' if j.get('title','') in [n['title'] for n in new] else ('🔧' if j['company']=='IBM UK' else '  ')
    print(f"  {fr} [{j['visa_sponsorship']}] {j['title'][:55]} | {j['company'][:30]} | {j['link_status']}")
