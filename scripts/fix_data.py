#!/usr/bin/env python3
"""Fix Konversational + add new finds"""
import json, os
TODAY = "2026-05-06"
OUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobs.json")

with open(OUT) as f:
    data = json.load(f)

jobs = data['jobs']

# FIX: Konversational says "No need for visa sponsorship" — NOT verified
for j in jobs:
    if 'konversational' in j['company'].lower():
        j['visa_sponsorship'] = 'unavailable'
        j['description'] = 'Boutique ServiceNow consultancy. Hands-on technical implementations. CSM certified. 144 applicants. ❌ Job listing states "No need for visa sponsorship" — not available for international candidates.'

# ADD: Capgemini Implementation Specialist (fresh from Hunt UK, posted Apr 29)
cap_new = {
    "title": "ServiceNow Implementation Specialist",
    "company": "Capgemini UK",
    "location": "England",
    "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
    "date_posted": "2026-04-29",
    "url": "https://huntukvisasponsors.com/job/servicenow-implementation-specialist-at-capgemini-occxnhvmrvw9",
    "fallback_url": "https://www.capgemini.com/gb-en/careers/",
    "source": "Hunt UK", "source_type": "direct",
    "role_type": "consultant", "remote": "hybrid", "employment": "permanent",
    "sc_clearance": True, "grad_scheme": False, "link_status": "live",
    "visa_sponsorship": "sc_blocked",
    "description": "Develop and integrate ServiceNow solutions across CSM, ITSM, ITOM, HRSD. JavaScript, Flow Designer, Integration Hub. SC clearance required — 5yr UK residency."
}

# ADD: Syntax Consultancy ServiceNow Developer (Totaljobs, 12-month FTC, Newbury)
syn_job = {
    "title": "ServiceNow Developer (12-month FTC)",
    "company": "Syntax Consultancy",
    "location": "Newbury, Berkshire",
    "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
    "date_posted": "2026-03-15",
    "url": "https://www.totaljobs.com/job/servicenow-developer/syntax-consultancy-limited-job106974694",
    "source": "Totaljobs", "source_type": "agency",
    "role_type": "developer", "remote": "hybrid", "employment": "contract",
    "sc_clearance": False, "grad_scheme": False, "link_status": "live",
    "visa_sponsorship": "agency_unknown",
    "description": "12-month fixed-term contract. Newbury-based, hybrid (3 days WFH, 2 days onsite). Start ASAP March/April 2026. Agency listing — verify sponsorship with employer."
}

# Dedup and add
seen_urls = {j.get('url','') for j in jobs}
if syn_job['url'] not in seen_urls:
    jobs.append(syn_job)
if cap_new['url'] not in seen_urls:
    jobs.append(cap_new)

result = {
    "updated": TODAY,
    "total": len(jobs),
    "verified": sum(1 for j in jobs if j["visa_sponsorship"] == "verified"),
    "sc_blocked": sum(1 for j in jobs if j["visa_sponsorship"] == "sc_blocked"),
    "unavailable": sum(1 for j in jobs if j["visa_sponsorship"] == "unavailable"),
    "grad_schemes": sum(1 for j in jobs if j["grad_scheme"]),
    "live_links": sum(1 for j in jobs if j["link_status"] == "live"),
    "fresh_today": 3,
    "sources": {},
    "jobs": jobs
}

# Count sources
srcs = {}
for j in jobs:
    s = j.get('source','?')
    srcs[s] = srcs.get(s, 0) + 1
result['sources'] = srcs

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"SAVED {len(jobs)} jobs")
for j in jobs:
    sp = j["visa_sponsorship"]
    print(f"  [{sp}] {j['title'][:55]} | {j['company']} | {j.get('link_status','?')}")
