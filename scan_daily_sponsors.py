#!/usr/bin/env python3
"""Run scan_sponsorship.py on the daily snapshot directly, then copy results back."""
import json, sys, os, csv
sys.path.insert(0, os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/scripts"))

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
TODAY = "2026-05-13"
DAILY_FILE = os.path.join(REPO, "daily", f"jobs_{TODAY}.json")
SPONSOR_CSV = os.path.expanduser("~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv")

# Load sponsor set
sponsors = set()
with open(SPONSOR_CSV, 'r', encoding='utf-8-sig') as f:
    for row in csv.DictReader(f):
        if 'skilled worker' in row.get('Route','').lower() and 'a rating' in row.get('Type & Rating','').lower():
            sponsors.add(row.get('Organisation Name','').strip().lower())
print(f"Loaded {len(sponsors)} sponsors")

# Load daily snapshot
with open(DAILY_FILE) as f:
    daily = json.load(f)

# Company matching logic
def normalize_company(name):
    n = name.lower().strip()
    for suffix in [' ltd', ' limited', ' plc', ' uk limited', ' uk', ' (uk)', '(uk)',
                   ' corporation', ' inc', ' incorporated', ' group', ' holdings',
                   ' services', ' solutions', ' technologies', ' consulting']:
        if n.endswith(suffix):
            n = n[:-len(suffix)].strip()
    import re
    n = re.sub(r'\s*\([^)]*\)\s*', ' ', n).strip()
    if ' - ' in n:
        n = n.split(' - ')[0].strip()
    return n

def company_has_licence(company_name):
    if not company_name:
        return False
    raw = company_name.lower().strip()
    if raw in sponsors:
        return True
    norm = normalize_company(company_name)
    if norm and norm in sponsors:
        return True
    if norm and len(norm) > 2:
        for s in sponsors:
            if norm in s or s in norm:
                return True
    return False

# Score each job
licence_count = 0
no_sponsor_patterns = [
    r'no\s+(visa\s+)?sponsorship',
    r'cannot\s+(provide\s+)?sponsor',
    r'unable\s+to\s+sponsor',
    r'does\s+not\s+(offer|provide)\s+(visa\s+)?sponsorship',
    r'no\s+need\s+for\s+visa\s+sponsorship',
    r'will\s+not\s+sponsor',
]

sc_patterns = [
    r'(?:security\s+clearance|sc\s+clear|sc\s+cleared|dv\s+clear|dv\s+cleared|developed\s+vetting)',
    r'must\s+be\s+eligible\s+for\s+(?:sc|security)\s+clearance',
    r'5\s+years?\s+(?:continuous\s+)?uk\s+residency',
    r'sc\s+(?:clearance|cleared)\s+(?:is\s+)?(?:required|essential|mandatory|needed)',
]

for j in daily['jobs']:
    company = j.get('company', '')
    desc = j.get('description', '')
    desc_lower = desc.lower()
    
    # Sponsor licence flag (DATA only, not visa_sponsorship tag)
    if company:
        has_licence = company_has_licence(company)
        if has_licence:
            j['sponsor_licence'] = True
            licence_count += 1
        # Don't set false
    
    # Text scan for SC/DV (overwrites visa_sponsorship only if found)
    for pattern in sc_patterns:
        import re
        if re.search(pattern, desc_lower):
            j['visa_sponsorship'] = 'sc_blocked'
            break
    
    # Text scan for "no sponsorship" 
    for pattern in no_sponsor_patterns:
        import re
        if re.search(pattern, desc_lower):
            j['visa_sponsorship'] = 'unavailable'
            break

# Recount
tags = {}
for j in daily['jobs']:
    t = j.get('visa_sponsorship', 'unknown')
    tags[t] = tags.get(t, 0) + 1

print(f"\nScanned {len(daily['jobs'])} jobs")
print(f"Sponsor licences flagged: {licence_count}")
print(f"Tags: {tags}")

# Save back
with open(DAILY_FILE, 'w') as f:
    json.dump(daily, f, indent=2, ensure_ascii=False)
print(f"✅ Updated daily snapshot with sponsor data")
