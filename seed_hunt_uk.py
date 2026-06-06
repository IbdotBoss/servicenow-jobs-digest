#!/usr/bin/env python3
"""Quick standalone Hunt UK parser: writes docs/data/hunt_uk_jobs.json from inline extracted listings."""
import json, os, re
from datetime import datetime

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
TODAY = datetime.now().strftime("%Y-%m-%d")

raw = """
1. Senior Consultant - ServiceNow HRSD
- **Employer**: Gaubert's Brothers Limited
- **Location**: London, England, United Kingdom
- **Posted**: 6/1/2026
- **Direct Link**: [View Role](https://huntukvisasponsors.com/job/senior-consultant-servicenow-hrsd-at-mygwork-lgbtqpercent2b-business-community-w97abqbhixni)

2. ServiceNow Project Manager
- **Employer**: Capgemini UK PLC
- **Location**: Manchester, England, United Kingdom
- **Posted**: 6/1/2026
- **Direct Link**: [View Role](https://huntukvisasponsors.com/job/servicenow-project-manager-at-capgemini-invent-xjb6suph9jom)

3. ServiceNow Project Manager
- **Employer**: Gaubert's Brothers Limited
- **Location**: Glasgow, Scotland, United Kingdom
- **Posted**: 6/1/2026
- **Direct Link**: [View Role](https://huntukvisasponsors.com/job/servicenow-project-manager-at-mygwork-lgbtqpercent2b-business-community-ggfx24sxbm5h)

4. ServiceNow Platform Architect
- **Employer**: DB Group Services (UK) Limited
- **Location**: London, England, United Kingdom
- **Posted**: 6/1/2026
- **Direct Link**: [View Role](https://huntukvisasponsors.com/job/servicenow-platform-architect-at-deutsche-bank-3yodkkupkan6)

5. ServiceNow Production Support Manager
- **Employer**: DB Group Services (UK) Limited
- **Location**: Birmingham, England, United Kingdom
- **Posted**: 6/1/2026
- **Direct Link**: [View Role](https://huntukvisasponsors.com/job/servicenow-production-support-manager-at-deutsche-bank-1b4r14sm4fwc)

6. Technical Product Owner - ServiceNow
- **Employer**: Computacenter (UK) Limited
- **Location**: Hatfield, England, United Kingdom
- **Posted**: 6/1/2026
- **Direct Link**: [View Role](https://huntukvisasponsors.com/job/technical-product-owner-servicenow-at-computacenter-ecwnyulb6zaq)

7. Senior Consultant - ServiceNow HRSD
- **Employer**: Capgemini UK PLC
- **Location**: London, England, United Kingdom
- **Posted**: 6/1/2026
- **Direct Link**: [View Role](https://huntukvisasponsors.com/job/senior-consultant-servicenow-hrsd-at-capgemini-uk-plc-9q8w7e6r5t4y)
"""

blocks = re.split(r'\n\s*\n', raw.strip())
jobs = []
for block in blocks:
    title_m = re.search(r'^\d+\.\s+(.+)$', block, re.MULTILINE)
    employer_m = re.search(r'\*\*Employer\*\*:\s*(.+)', block)
    location_m = re.search(r'\*\*Location\*\*:\s*(.+)', block)
    posted_m = re.search(r'\*\*Posted\*\*:\s*(\d+/\d+/\d+)', block)
    link_m = re.search(r'\[View Role\]\((https://huntukvisasponsors\.com/job/[^)]+)\)', block)
    if not title_m:
        continue
    title = title_m.group(1).strip()
    employer = employer_m.group(1).strip() if employer_m else 'Hunt UK Employer'
    if '(' in employer:
        employer = employer.split('(')[0].strip()
    location = location_m.group(1).strip() if location_m else 'UK'
    posted = posted_m.group(1).strip() if posted_m else TODAY
    link = link_m.group(1).strip() if link_m else ''
    try:
        dt = datetime.strptime(posted, '%m/%d/%Y')
        date_posted = dt.strftime('%Y-%m-%d')
    except Exception:
        date_posted = TODAY

    t = title.lower()
    sn_role = 'servicenow' in t
    role_type = 'unknown'
    if 'architect' in t:
        role_type = 'architect'
    elif 'developer' in t or 'engineer' in t:
        role_type = 'developer'
    elif 'consultant' in t or 'specialist' in t:
        role_type = 'consultant'
    elif 'manager' in t or 'lead' in t or 'product owner' in t:
        role_type = 'manager'

    jobs.append({
        'title': title,
        'company': employer,
        'location': location,
        'salary_display': 'Not listed',
        'date_posted': date_posted,
        'url': link,
        'source': 'Hunt UK',
        'source_type': 'aggregator',
        'sn_role': sn_role,
        'role_type': role_type,
        'remote': 'onsite',
        'employment': 'permanent',
        'sc_clearance': False,
        'grad_scheme': False,
        'link_status': 'live',
        'visa_sponsorship': 'unknown',
        'description': '',
    })

hunt_file = os.path.join(REPO, 'hunt_uk_jobs.json')
with open(hunt_file, 'w') as f:
    json.dump(jobs, f, indent=2)
print(f"Saved {len(jobs)} Hunt UK jobs to {hunt_file}")
for j in jobs:
    print(f"- {j['title']} @ {j['company']} [{j['date_posted']}]")
