#!/usr/bin/env python3
"""Final comprehensive data update — all sources searched"""
import json, os

TODAY = "2026-05-06"
OUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobs.json")

with open(OUT) as f:
    data = json.load(f)

# Fix existing Konversational
for j in data['jobs']:
    if 'konversational' in j['company'].lower():
        j['visa_sponsorship'] = 'unavailable'
        j['description'] = 'Boutique ServiceNow consultancy. CSM certified. ❌ Job listing states "No need for visa sponsorship" — not available for international candidates.'

# New jobs from today's search across ALL sources
new_jobs = [
    # ── Deerfoot (searched directly) ──
    {
        "title": "ServiceNow Developer",
        "company": "Deerfoot (agency)",
        "location": "London / UK-wide",
        "salary_display": "£70,000-£120,000", "salary_min": 70000, "salary_max": 120000,
        "date_posted": TODAY,
        "url": "https://www.deerfoot.co.uk/jobs",
        "source": "Deerfoot", "source_type": "agency",
        "role_type": "developer", "remote": "hybrid", "employment": "permanent",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "RPA, ServiceNow Virtual Agent, ITSM, ITOM, JavaScript. UK-wide offices, hybrid 2 days onsite. Deerfoot is a recruitment agency — verify sponsorship with actual employer."
    },
    
    # ── Akkodis IRM/SecOps (searched directly) ──
    {
        "title": "ServiceNow IRM / SecOps Technical Consultant",
        "company": "Akkodis (agency)",
        "location": "UK — Remote",
        "salary_display": "£50,000-£90,000", "salary_min": 50000, "salary_max": 90000,
        "date_posted": TODAY,
        "url": "https://www.akkodis.com/en-gb/careers/jobs/servicenow-irm-or-secops-technical-consultants-remote-/BROADBEAN_991481777472788",
        "source": "Akkodis", "source_type": "agency",
        "role_type": "consultant", "remote": "remote", "employment": "permanent",
        "sc_clearance": True, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "sc_blocked",
        "description": "IRM (Risk, Policy & Compliance, Vendor Risk, Audit) and SecOps. Must be eligible for Security Clearance. Akkodis is an agency — SC requirement blocks sponsorship."
    },
    
    # ── Glasgow Bank SN HR Developer (ComputerJobs, Morgan McKinley) ──
    {
        "title": "ServiceNow HR Developer (HRSD)",
        "company": "Major Bank via Morgan McKinley",
        "location": "Glasgow",
        "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
        "date_posted": "2026-04-28",
        "url": "https://uk.computerjobs.com/search-jobs-in-Glasgow-Lanarkshire-GBR/SERVICENOW-HR-DEVELOPER-384bfd9a7018af3f3f/",
        "source": "ComputerJobs", "source_type": "agency",
        "role_type": "developer", "remote": "onsite", "employment": "permanent",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "Leading bank, Glasgow (3+ days onsite). HRSD platform development. Morgan McKinley agency. Employer likely Barclays or Morgan Stanley — both hold A-rated sponsor licences. Verify sponsorship with employer."
    },
    
    # ── Syntax Consultancy SN Architect (CV-Library) ──
    {
        "title": "ServiceNow Architect",
        "company": "Syntax Consultancy (agency)",
        "location": "Newbury, Berkshire",
        "salary_display": "£90,000-£100,000", "salary_min": 90000, "salary_max": 100000,
        "date_posted": "2026-04-25",
        "url": "https://www.cv-library.co.uk/job/225046257/ServiceNow-Architect",
        "source": "CV-Library", "source_type": "agency",
        "role_type": "architect", "remote": "hybrid", "employment": "permanent",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "12-month FTC, hybrid 2 days remote. May/June 2026 start. Syntax Consultancy NOT on sponsor register — verify sponsorship with actual employer."
    },
    
    # ── Hays SN Solution Architect (SC cleared, contract) ──
    {
        "title": "ServiceNow Solution Architect (SC Cleared)",
        "company": "Hays (agency)",
        "location": "UK — Remote",
        "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
        "date_posted": "2026-04-20",
        "url": "https://www.hays.co.uk/job-detail/servicenow-solution-architect-united-kingdom_4776886",
        "source": "Hays", "source_type": "agency",
        "role_type": "architect", "remote": "remote", "employment": "contract",
        "sc_clearance": True, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "sc_blocked",
        "description": "Design end-to-end ServiceNow solutions across ITSM, ITOM. Contract, remote. Requires existing SC Clearance — blocks international candidates."
    },
    
    # ── Hays SN Technical Consultant (Computacenter, Milton Keynes) ──
    {
        "title": "ServiceNow Technical Consultant",
        "company": "Computacenter via Hays",
        "location": "Milton Keynes",
        "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
        "date_posted": "2026-04-15",
        "url": "https://www.hays.co.uk/job-detail/consultant-(non-ps)-milton-keynes_4767977",
        "source": "Hays", "source_type": "agency",
        "role_type": "consultant", "remote": "hybrid", "employment": "permanent",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "Computacenter — Elite ServiceNow Partner. Computacenter UK is on the sponsor register (A-rated). Verify sponsorship for this specific role."
    },
    
    # ── Capgemini Implementation Specialist (Hunt UK, Apr 29) ──
    {
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
        "description": "CSM, ITSM, ITOM, HRSD. JavaScript, Flow Designer. SC clearance required — 5yr UK residency. Not available for international candidates."
    },
]

# Dedup and merge
seen = {j.get('url','') for j in data['jobs']}
for nj in new_jobs:
    if nj['url'] not in seen:
        data['jobs'].append(nj)
        seen.add(nj['url'])

data['updated'] = TODAY
data['total'] = len(data['jobs'])
data['verified'] = sum(1 for j in data['jobs'] if j['visa_sponsorship'] == 'verified')
data['sc_blocked'] = sum(1 for j in data['jobs'] if j['visa_sponsorship'] == 'sc_blocked')
data['unavailable'] = sum(1 for j in data['jobs'] if j['visa_sponsorship'] == 'unavailable')
data['grad_schemes'] = sum(1 for j in data['jobs'] if j['grad_scheme'])
data['live_links'] = sum(1 for j in data['jobs'] if j['link_status'] == 'live')
data['fresh_today'] = len(new_jobs)
data['sources_searched'] = 15

srcs = {}
for j in data['jobs']:
    s = j.get('source','?')
    srcs[s] = srcs.get(s, 0) + 1
data['sources'] = srcs

os.makedirs(os.path.dirname(OUT), exist_ok=True)
with open(OUT, 'w') as f:
    json.dump(data, f, indent=2, ensure_ascii=False)

print(f"SAVED {len(data['jobs'])} jobs from {len(srcs)} sources")
print(f"  Verified: {data['verified']} | SC blocked: {data['sc_blocked']} | Unavailable: {data['unavailable']} | Agency: {sum(1 for j in data['jobs'] if j['visa_sponsorship']=='agency_unknown')}")
for j in data['jobs']:
    sp = j['visa_sponsorship']
    print(f"  [{sp}] {j['title'][:55]} | {j['company'][:30]} | {j.get('source','?')}")
