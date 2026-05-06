#!/usr/bin/env python3
"""Emergency fresh data update"""
import json, os

TODAY = "2026-05-06"
OUTPUT = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data/jobs.json")

jobs = [
    # ── FRESH: Posted hours/days ago ──
    {
        "title": "ServiceNow Technical Consultant",
        "company": "Konversational",
        "location": "Greater London",
        "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
        "date_posted": TODAY,
        "url": "https://uk.linkedin.com/jobs/view/servicenow-technical-consultant-at-konversational-the-servicenow-customer-workflow-experts-4398113003",
        "source": "LinkedIn", "source_type": "direct",
        "role_type": "consultant", "remote": "hybrid", "employment": "permanent",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "verified",
        "description": "Boutique ServiceNow consultancy. Hands-on technical implementations on ServiceNow platform. Customer workflow experts. 144 applicants."
    },
    {
        "title": "ServiceNow Developer",
        "company": "Experis (ManpowerGroup)",
        "location": "UK — Remote",
        "salary_display": "£45,000-£48,000", "salary_min": 45000, "salary_max": 48000,
        "date_posted": "2026-05-03",
        "url": "https://www.experis.co.uk/job/servicenow-developer-5892809",
        "fallback_url": "https://uk.linkedin.com/jobs/view/servicenow-developer-at-experis-uk-4409552917",
        "source": "Experis", "source_type": "agency",
        "role_type": "developer", "remote": "remote", "employment": "permanent",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "ServiceNow Developer. Remote (must be UK-based). £45k-£48k. 12-month fixed term contract initially. Analyse and understand ServiceNow environments."
    },
    {
        "title": "ServiceNow HR Developer (Contract to Dec 2026)",
        "company": "hackajob",
        "location": "London",
        "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
        "date_posted": "2026-05-03",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-hr-developer-full-time-contract-ending-in-december-2026-at-hackajob-4407923549",
        "source": "LinkedIn", "source_type": "agency",
        "role_type": "developer", "remote": "hybrid", "employment": "contract",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "Full-time contract ending December 2026. HR Service Delivery module. hackajob is a recruitment platform — verify sponsorship with actual employer."
    },
    
    # ── Verified sponsor, no SC blocker ──
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
        "sc_clearance": False, "grad_scheme": False, "link_status": "expired",
        "visa_sponsorship": "verified",
        "description": "IBM Consulting. Hybrid cloud and AI journeys. Check IBM careers page for current ServiceNow openings."
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
        "sc_clearance": False, "grad_scheme": False, "link_status": "expired",
        "visa_sponsorship": "verified",
        "description": "Maintenance, configuration and development of the Firm's ITSM tool. Check Clifford Chance careers page."
    },
    
    # ── SC blocked — can't sponsor ──
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
        "sc_clearance": True, "grad_scheme": False, "link_status": "expired",
        "visa_sponsorship": "sc_blocked",
        "description": "SC clearance required — 5yr UK residency. Not available for international candidates."
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
        "sc_clearance": True, "grad_scheme": False, "link_status": "expired",
        "visa_sponsorship": "sc_blocked",
        "description": "SC clearance required — 5yr UK residency. Not available for international candidates."
    },
    
    # ── Grad ──
    {
        "title": "Graduate ServiceNow Technical Consultant 2026",
        "company": "Capgemini",
        "location": "London",
        "salary_display": "£30,000", "salary_min": 30000, "salary_max": 30000,
        "date_posted": "2026-03-15",
        "url": "https://www.capgemini.com/gb-en/careers/",
        "source": "Capgemini Careers", "source_type": "direct",
        "role_type": "consultant", "remote": "hybrid", "employment": "permanent",
        "sc_clearance": False, "grad_scheme": True, "link_status": "live",
        "visa_sponsorship": "verified",
        "description": "Sep 2026 start. £30,000 salary. Training & development. ServiceNow platform solutions."
    },
    
    # ── Agency, stale ──
    {
        "title": "ServiceNow Consultant - ITAM",
        "company": "Marshall Wolfe",
        "location": "Manchester",
        "salary_display": "£90,000-£110,000", "salary_min": 90000, "salary_max": 110000,
        "date_posted": "2026-04-16",
        "url": "https://www.reed.co.uk/jobs/servicenow-consultant-itam/56782227",
        "source": "Reed", "source_type": "agency",
        "role_type": "consultant", "remote": "hybrid", "employment": "permanent",
        "sc_clearance": False, "grad_scheme": False, "link_status": "live",
        "visa_sponsorship": "agency_unknown",
        "description": "ITAM Product Manager - ServiceNow HAM/SAM. Posted by recruitment agency — verify sponsorship with actual employer."
    },
    
    # ── Stale ──
    {
        "title": "ServiceNow Developer",
        "company": "Akoni Technologies",
        "location": "Reading, Berkshire",
        "salary_display": "Not listed", "salary_min": 0, "salary_max": 0,
        "date_posted": "2026-01-06",
        "url": "https://uk.linkedin.com/jobs/view/servicenow-developer-at-akoni-technologies-3830988858",
        "source": "LinkedIn", "source_type": "direct",
        "role_type": "developer", "remote": "onsite", "employment": "permanent",
        "sc_clearance": False, "grad_scheme": False, "link_status": "stale",
        "visa_sponsorship": "verified",
        "description": "Visa Sponsorship (Skilled Worker Visa) can be provided. Posted January — may be filled."
    },
]

result = {
    "updated": TODAY,
    "total": len(jobs),
    "verified": sum(1 for j in jobs if j["visa_sponsorship"] == "verified"),
    "sc_blocked": sum(1 for j in jobs if j["visa_sponsorship"] == "sc_blocked"),
    "grad_schemes": sum(1 for j in jobs if j["grad_scheme"]),
    "live_links": sum(1 for j in jobs if j["link_status"] == "live"),
    "fresh_today": 3,
    "sources": {
        "reed": sum(1 for j in jobs if j["source"] == "Reed"),
        "hunt_uk": sum(1 for j in jobs if j["source"] == "Hunt UK"),
        "linkedin": sum(1 for j in jobs if j["source"] == "LinkedIn"),
        "other": sum(1 for j in jobs if j["source"] not in ["Reed", "Hunt UK", "LinkedIn"]),
    },
    "jobs": jobs
}

os.makedirs(os.path.dirname(OUTPUT), exist_ok=True)
with open(OUTPUT, 'w') as f:
    json.dump(result, f, indent=2, ensure_ascii=False)

print(f"SAVED {len(jobs)} jobs")
for j in jobs:
    fresh = "🆕" if j["date_posted"] >= "2026-05-01" else "  "
    sp = j["visa_sponsorship"]
    print(f"  {fresh} [{sp}] {j['title'][:50]} | {j['company']} | {j['link_status']}")
