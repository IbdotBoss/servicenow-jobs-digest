#!/usr/bin/env python3
"""
Rebuild master.json from all daily snapshot files.
Each daily file is immutable — master is always rebuildable.
No state corruption possible.

Usage: python3 scripts/rebuild_master.py
"""

import json, os, glob
from datetime import datetime, timedelta
from collections import Counter

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
DAILY_DIR = os.path.join(REPO, "daily")
MASTER_FILE = os.path.join(REPO, "master.json")
JOBS_FILE = os.path.join(REPO, "jobs.json")  # active jobs copy for index page

TODAY = datetime.now().strftime("%Y-%m-%d")
STALE_DAYS = 7
EXPIRED_DAYS = 30

def job_key(job):
    title = job.get('title', '').lower().strip()
    company = job.get('company', '').lower().strip()
    for suffix in [' - the servicenow customer workflow experts', ' (agency)', ' via hays', ' via sthree']:
        company = company.replace(suffix, '')
    return f"{title}|{company}"

def rebuild():
    # Load all daily files
    daily_files = sorted(glob.glob(os.path.join(DAILY_DIR, "jobs_*.json")))
    if not daily_files:
        print("No daily files found. Create daily/jobs_YYYY-MM-DD.json first.")
        return None
    
    print(f"Loading {len(daily_files)} daily snapshots...")
    
    # Aggregate: job_key → {best job data, seen_dates}
    all_jobs = {}
    daily_dates = []
    
    for fpath in daily_files:
        fname = os.path.basename(fpath)
        date_str = fname.replace("jobs_", "").replace(".json", "")
        daily_dates.append(date_str)
        
        with open(fpath) as f:
            data = json.load(f)
        
        for j in data.get('jobs', []):
            key = job_key(j)
            if key not in all_jobs:
                j['first_seen'] = date_str
                j['last_seen'] = date_str
                j.setdefault('sources', [j.get('source', 'unknown')])
                all_jobs[key] = j
            else:
                existing = all_jobs[key]
                existing['last_seen'] = date_str
                # Merge sources
                src = j.get('source', '')
                if src and src not in existing.get('sources', []):
                    existing.setdefault('sources', []).append(src)
                # Update mutable fields from newest
                for field in ['salary_display', 'salary_min', 'salary_max', 'url', 'location']:
                    if j.get(field):
                        existing[field] = j[field]
                # Better sponsorship tag wins
                if j.get('visa_sponsorship') not in ('unknown', 'agency_unknown', None):
                    existing['visa_sponsorship'] = j['visa_sponsorship']
    
    # Convert to list and compute status
    jobs_list = list(all_jobs.values())
    for j in jobs_list:
        days_since = (datetime.now() - datetime.strptime(j['last_seen'], "%Y-%m-%d")).days
        if days_since > EXPIRED_DAYS:
            j['status'] = 'expired'
        elif days_since > STALE_DAYS:
            j['status'] = 'stale'
        else:
            j['status'] = 'active'
    
    # Sort: newest first_seen first
    jobs_list.sort(key=lambda j: j['first_seen'], reverse=True)
    
    # Build master
    tags = Counter(j.get('visa_sponsorship', 'unknown') for j in jobs_list)
    sources = Counter()
    for j in jobs_list:
        for s in j.get('sources', [j.get('source', 'unknown')]):
            sources[s] += 1
    
    master = {
        "updated": TODAY,
        "total": len(jobs_list),
        "total_active": sum(1 for j in jobs_list if j['status'] == 'active'),
        "verified": tags.get('sponsor_verified', 0) + tags.get('verified', 0),
        "sc_blocked": tags.get('sc_blocked', 0),
        "daily_snapshots": daily_dates,
        "sources": dict(sources.most_common(20)),
        "jobs": jobs_list
    }
    
    # Save
    with open(MASTER_FILE, 'w') as f:
        json.dump(master, f, indent=2)
    
    # Active-only copy for index page
    active = [j for j in jobs_list if j['status'] == 'active']
    active_master = {**master, "total": len(active), "jobs": active}
    with open(JOBS_FILE, 'w') as f:
        json.dump(active_master, f, indent=2)
    
    print(f"  Master: {master['total']} total jobs ({master['total_active']} active)")
    print(f"  Sponsors: {master['verified']} | SC-blocked: {master['sc_blocked']}")
    print(f"  Sources: {dict(sources.most_common(5))}")
    print(f"  Snapshots: {daily_dates[0]} → {daily_dates[-1]}")
    
    return master

if __name__ == '__main__':
    rebuild()
