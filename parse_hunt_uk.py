import json, os, re
from datetime import datetime

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
TMP = os.path.join(REPO, "hunt_uk_raw.json")
TODAY = datetime.now().strftime("%Y-%m-%d")

# Parse the saved web_extract result
with open(TMP) as f:
    data = json.load(f)

content = data["results"][0]["content"]
url = data["results"][0]["url"]

jobs = []
# Split by job number headings
blocks = re.split(r'\n### \d+\. ', content)
for block in blocks[1:]:
    title_m = re.search(r'^(.*?)(?:\n|$)', block)
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
