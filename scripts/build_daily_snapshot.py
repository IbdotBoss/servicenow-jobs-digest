#!/usr/bin/env python3
"""Build daily snapshot from all 5 sources into docs/data/daily/jobs_YYYY-MM-DD.json."""
import json, os
from datetime import datetime

TODAY = "2026-05-18"
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
        j.setdefault('source', 'JobServe')
        j.setdefault('source_type', 'aggregator')
        j.setdefault('date_posted', j.get('date_posted', TODAY))
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
        j.setdefault('source', 'LinkedIn')
        j.setdefault('source_type', 'direct')
        j.setdefault('date_posted', j.get('date_posted', TODAY))
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

# 3. Reed (deprecated, still read if present)
reed_file = os.path.join(REPO, "jobs.json")
if os.path.exists(reed_file):
    with open(reed_file) as f:
        reed_data = json.load(f)
    reed_jobs = reed_data.get('jobs', []) if isinstance(reed_data, dict) else reed_data
    for j in reed_jobs:
        j.setdefault('source', 'Reed')
        j.setdefault('source_type', 'agency' if j.get('source_type') == 'agency' else 'direct')
        j.setdefault('visa_sponsorship', 'agency_unknown' if j.get('source_type') == 'agency' else 'unknown')
        j.setdefault('sc_clearance', False)
        j.setdefault('grad_scheme', False)
        j.setdefault('link_status', 'live')
    all_jobs.extend(reed_jobs)
    source_counts['Reed'] = len(reed_jobs)
    print(f"Reed: {len(reed_jobs)} jobs")

# 4. ServiceNow Careers RSS
snc_file = os.path.join(REPO, "servicenow_careers_jobs.json")
if os.path.exists(snc_file):
    with open(snc_file) as f:
        snc_jobs = json.load(f)
    for j in snc_jobs:
        j.setdefault('source', 'ServiceNow Careers')
        j.setdefault('source_type', 'direct')
        j.setdefault('sn_role', True)
        j.setdefault('date_posted', j.get('date_posted', TODAY))
        j.setdefault('visa_sponsorship', 'unknown')
        j.setdefault('salary_display', 'Not listed')
        j.setdefault('role_type', 'unknown')
        j.setdefault('remote', 'onsite')
        j.setdefault('employment', 'permanent')
        j.setdefault('sc_clearance', False)
        j.setdefault('grad_scheme', False)
        j.setdefault('link_status', 'live')
        j.setdefault('description', '')
    all_jobs.extend(snc_jobs)
    source_counts['ServiceNow Careers'] = len(snc_jobs)
    print(f"ServiceNow Careers: {len(snc_jobs)} jobs")

# 5. Nelson Frank
nf_file = os.path.join(REPO, "nelson_frank_jobs.json")
if os.path.exists(nf_file):
    with open(nf_file) as f:
        nf_jobs = json.load(f)
    for j in nf_jobs:
        j.setdefault('source', 'Nelson Frank')
        j.setdefault('source_type', 'agency')
        j.setdefault('date_posted', j.get('date_posted', TODAY))
        j.setdefault('role_type', 'unknown')
        j.setdefault('remote', 'onsite')
        j.setdefault('employment', 'permanent')
        j.setdefault('link_status', 'live')
        j.setdefault('scraped_at', TODAY)
    all_jobs.extend(nf_jobs)
    source_counts['Nelson Frank'] = len(nf_jobs)
    print(f"Nelson Frank: {len(nf_jobs)} jobs")

# 6. Hunt UK (read from current hunt_uk_jobs.json)
hunt_uk_file = os.path.join(REPO, "hunt_uk_jobs.json")
if os.path.exists(hunt_uk_file):
    with open(hunt_uk_file) as f:
        hunt_uk_jobs = json.load(f)
    for j in hunt_uk_jobs:
        j.setdefault('source', 'Hunt UK')
        j.setdefault('source_type', 'aggregator')
        j.setdefault('date_posted', j.get('date_posted', TODAY))
        j.setdefault('visa_sponsorship', 'unknown')
        j.setdefault('sc_clearance', False)
        j.setdefault('grad_scheme', False)
        j.setdefault('link_status', 'live')
        j.setdefault('description', '')
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
print(f"   Unknown: {tags.get('unknown', 0)} | agency_unknown: {tags.get('agency_unknown', 0)} | SC-blocked pre-scan: {tags.get('sc_blocked', 0)}")
