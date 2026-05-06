#!/usr/bin/env python3
"""Generate unified jobs.json from Reed + Hunt UK + Sponsor CSV"""
import json, os
from datetime import datetime

TODAY = "2026-05-06"
OUTPUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobs.json")

jobs = [
    # ── Reed ──
    {
        "id": "reed-1",
        "title": "ServiceNow Consultant - ITAM",
        "company": "Marshall Wolfe",
        "location": "Manchester",
        "county": "Lancashire",
        "salary_min": 90000, "salary_max": 110000,
        "salary_display": "£90k-£110k",
        "date_posted": "2026-04-16",
        "url": "https://www.reed.co.uk/jobs/servicenow-consultant-itam/56782227",
        "source": "Reed",
        "source_type": "agency",
        "role_type": "consultant",
        "remote": "hybrid",
        "employment": "permanent",
        "description": "ITAM Product Manager - ServiceNow HAM/SAM. Working with technology teams to improve IT service management processes.",
        "sc_clearance": False,
        "grad_scheme": False,
        "visa_sponsorship": "unknown"
    },
    {
        "id": "reed-2",
        "title": "ServiceNow Architect - Telecoms",
        "company": "eFinancialCareers",
        "location": "London",
        "county": "London",
        "salary_min": 20000, "salary_max": 100000,
        "salary_display": "£20k-£100k",
        "date_posted": "2026-04-18",
        "url": "https://www.reed.co.uk/jobs/servicenow-architect-morgan-mckinley/56856789",
        "source": "Reed",
        "source_type": "agency",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "contract",
        "description": "Enterprise Architect - ServiceNow (Telecoms). Inside IR35. 6-Month Contract. Leading consultancy on a high-profile telecoms transformation programme.",
        "sc_clearance": False,
        "grad_scheme": False,
        "visa_sponsorship": "unknown"
    },
    
    # ── Hunt UK (verified sponsors) ──
    {
        "id": "hunt-1",
        "title": "ServiceNow Developer, AVP",
        "company": "State Street Bank",
        "location": "London",
        "county": "London",
        "salary_min": 0, "salary_max": 0,
        "salary_display": "Not listed",
        "date_posted": "2026-04-22",
        "url": "https://huntukvisasponsors.com/job/servicenow-developer-at-state-street-bank-and-trust-company-4b6mxtzqt4t",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "developer",
        "remote": "hybrid",
        "employment": "permanent",
        "description": "Design, build, and customize ServiceNow platform applications. Member of a geographically distributed team of ServiceNow developers and administrators.",
        "sc_clearance": True,
        "grad_scheme": False,
        "visa_sponsorship": "verified"
    },
    {
        "id": "hunt-2",
        "title": "ServiceNow Senior Developer (11m Contract)",
        "company": "Clifford Chance (Gaubert's Brothers)",
        "location": "UK",
        "county": "",
        "salary_min": 0, "salary_max": 0,
        "salary_display": "Not listed",
        "date_posted": "2026-04-22",
        "url": "https://huntukvisasponsors.com/job/servicenow-senior-developer-11-months-contract-at-gauberts-brothers-limited-ru0et0agp9ly",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "developer",
        "remote": "hybrid",
        "employment": "contract",
        "description": "Maintenance, configuration and development of the Firm's IT Service Management tool, ServiceNow. Working within an agreed governance model.",
        "sc_clearance": False,
        "grad_scheme": False,
        "visa_sponsorship": "verified"
    },
    {
        "id": "hunt-3",
        "title": "ServiceNow Developer",
        "company": "Capgemini UK",
        "location": "London",
        "county": "London",
        "salary_min": 0, "salary_max": 0,
        "salary_display": "Not listed",
        "date_posted": "2026-04-14",
        "url": "https://huntukvisasponsors.com/job/servicenow-developer-at-capgemini-uk-plc-dvetgmhjcls",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "developer",
        "remote": "hybrid",
        "employment": "permanent",
        "description": "Design, develop, and maintain ServiceNow applications. Virtual Agent, RPA flows. JavaScript, ITSM, ITOM. Hybrid working — blend of offices, client sites, home.",
        "sc_clearance": True,
        "grad_scheme": False,
        "visa_sponsorship": "verified"
    },
    {
        "id": "hunt-4",
        "title": "Senior ServiceNow Developer / Architect",
        "company": "IBM UK",
        "location": "UK",
        "county": "",
        "salary_min": 0, "salary_max": 0,
        "salary_display": "Not listed",
        "date_posted": "2026-04-22",
        "url": "https://huntukvisasponsors.com/job/senior-servicenow-developer-architect-at-ibm-uk-ltd-q6eu3tyaitdl",
        "source": "Hunt UK",
        "source_type": "direct",
        "role_type": "architect",
        "remote": "hybrid",
        "employment": "permanent",
        "description": "IBM Consulting. Long-term client relationships and close collaboration worldwide. Hybrid cloud and AI journeys with strategic partners and IBM technology.",
        "sc_clearance": False,
        "grad_scheme": False,
        "visa_sponsorship": "verified"
    },
    
    # ── LinkedIn (confirmed via web_search) ──
    {
        "id": "li-1",
        "title": "ServiceNow Developer",
        "company": "Akoni Technologies",
        "location": "Reading",
        "county": "Berkshire",
        "salary_min": 0, "salary_max": 0,
        "salary_display": "Not listed",
        "date_posted": "2026-01-06",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-developer-at-akoni-technologies-3830988858",
        "source": "LinkedIn",
        "source_type": "direct",
        "role_type": "developer",
        "remote": "onsite",
        "employment": "permanent",
        "description": "Service Now Developer — hands-on experience designing and developing solutions. Visa Sponsorship (Skilled Worker Visa) can be provided.",
        "sc_clearance": False,
        "grad_scheme": False,
        "visa_sponsorship": "verified"
    },
    
    # ── Grad Schemes ──
    {
        "id": "grad-1",
        "title": "Graduate ServiceNow Technical Consultant 2026",
        "company": "Capgemini",
        "location": "London",
        "county": "London",
        "salary_min": 30000, "salary_max": 30000,
        "salary_display": "£30,000",
        "date_posted": "2026-03-15",
        "url": "https://www.brightnetwork.co.uk/graduate-jobs/capgemini-invent/graduate-servicenow-technical-consultant-2026",
        "source": "Bright Network",
        "source_type": "direct",
        "role_type": "consultant",
        "remote": "hybrid",
        "employment": "permanent",
        "description": "Sep 2026 start. £30,000 salary. Training & development included. ServiceNow platform solutions for clients across industries.",
        "sc_clearance": False,
        "grad_scheme": True,
        "visa_sponsorship": "verified"
    },
    {
        "id": "grad-2",
        "title": "EMEA Solution Consulting Intern (Jun 2026)",
        "company": "ServiceNow UK",
        "location": "Staines",
        "county": "Surrey",
        "salary_min": 0, "salary_max": 0,
        "salary_display": "Not listed",
        "date_posted": "2026-03-01",
        "url": "https://uk.prosple.com/graduate-employers/servicenow-uk/jobs-internships/emea-solution-consulting-intern",
        "source": "Prosple",
        "source_type": "direct",
        "role_type": "consultant",
        "remote": "hybrid",
        "employment": "internship",
        "description": "Support transformational programs and enhance pre-sales engagement at a global technology leader. EMEA Solution Consulting team.",
        "sc_clearance": False,
        "grad_scheme": True,
        "visa_sponsorship": "verified"
    },
]

# Save
os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, 'w') as f:
    json.dump({
        'updated': TODAY,
        'total': len(jobs),
        'sponsored': sum(1 for j in jobs if j['visa_sponsorship'] == 'verified'),
        'grad_schemes': sum(1 for j in jobs if j['grad_scheme']),
        'sc_clearance': sum(1 for j in jobs if j['sc_clearance']),
        'sources': {
            'reed': sum(1 for j in jobs if j['source'] == 'Reed'),
            'hunt_uk': sum(1 for j in jobs if j['source'] == 'Hunt UK'),
            'linkedin': sum(1 for j in jobs if j['source'] == 'LinkedIn'),
            'other': sum(1 for j in jobs if j['source'] not in ['Reed', 'Hunt UK', 'LinkedIn']),
        },
        'jobs': jobs
    }, f, indent=2)

print(f"Saved {len(jobs)} jobs to {OUTPUT}")
for j in jobs:
    badges = []
    if j['visa_sponsorship'] == 'verified': badges.append('🏷️ SPONSORED')
    if j['grad_scheme']: badges.append('🎓 GRAD')
    if j['sc_clearance']: badges.append('🔒 SC')
    print(f"  {j['title'][:60]} | {j['company'][:25]} | {j['source']} | {' '.join(badges)}")
