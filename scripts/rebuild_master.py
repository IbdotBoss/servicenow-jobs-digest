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
STALE_DAYS = 14
EXPIRED_DAYS = 60

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

        if isinstance(data, list):
            jobs_iter = data
        elif isinstance(data, dict):
            jobs_iter = data.get('jobs', [])
        else:
            print(f"  [WARN] Unexpected data type in {fname}, skipping")
            continue

        for j in jobs_iter:
            # Normalize old tag format — map legacy tags to unknown
            tag = j.get('visa_sponsorship', 'unknown')
            if tag == 'sponsor_verified':
                j['visa_sponsorship'] = 'unknown'
                tag = 'unknown'
            
            key = job_key(j)
            if key not in all_jobs:
                j['first_seen'] = date_str
                j['last_seen'] = date_str
                j.setdefault('sources', [j.get('source', 'unknown')])
                j.setdefault('sponsor_licence', False)
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
                # Propagate sponsor_licence: once true, stays true
                if j.get('sponsor_licence'):
                    existing['sponsor_licence'] = True
                # Propagate sponsorship_mentioned: once true, stays true
                if j.get('sponsorship_mentioned'):
                    existing['sponsorship_mentioned'] = True
                # Better sponsorship tag wins
                if tag not in ('unknown', 'agency_unknown', None):
                    existing['visa_sponsorship'] = tag
    
    # Convert to list and compute status
    jobs_list = list(all_jobs.values())
    
    # Dead sources — jobs from these are always expired
    DEAD_SOURCES = ['ComputerJobs', 'Totaljobs', 'CV-Library', 'Deerfoot', 'Reed']
    
    BAD_URL_PATTERNS = ['/mob/JobSearch/Results?q=', 'huntukvisasponsors.com/jobs?q=',
                        'huntukvisasponsors.com/company/', 'computerjobs.com',
                        'totaljobs.com', 'cv-library.co.uk', 'deerfoot.co.uk/jobs']
    for j in jobs_list:
        # Propagate sponsor_licence from any daily snapshot
        j.setdefault('sponsor_licence', False)
        
        # Fix: if date_posted is missing, use first_seen
        if not j.get('date_posted'):
            j['date_posted'] = j.get('first_seen', TODAY)
        
        days_since = (datetime.now() - datetime.strptime(j['last_seen'], "%Y-%m-%d")).days
        
        # Dead source → expired
        if j.get('source', '') in DEAD_SOURCES:
            j['status'] = 'expired'
            j['link_status'] = 'expired'
        # Empty or missing URL → expired
        elif not j.get('url') or len(j.get('url', '').strip()) < 5:
            j['status'] = 'expired'
            j['link_status'] = 'expired'
        elif days_since > EXPIRED_DAYS:
            j['status'] = 'expired'
        elif days_since > STALE_DAYS:
            j['status'] = 'stale'
            j['link_status'] = 'stale'
        else:
            j['status'] = 'active'
        
        # Also expire jobs with bad/unfixable URLs
        url = j.get('url', '')
        for p in BAD_URL_PATTERNS:
            if p in url:
                j['status'] = 'expired'
                j['link_status'] = 'expired'
                break
    
    # Sort: newest first_seen first
    jobs_list.sort(key=lambda j: j['first_seen'], reverse=True)
    
    # SAFETY NET: Normalize legacy tags — strip any 'verified'/'sponsor_verified'
    #   No algorithm claims sponsorship. Only sponsor_licence (CSV cross-ref) is auto-set.
    for j in jobs_list:
        sp = j.get('visa_sponsorship', 'unknown')
        if sp in ('verified', 'sponsor_verified'):
            j['visa_sponsorship'] = 'unknown'
    
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
        "licenced_sponsors": sum(1 for j in jobs_list if j.get('sponsor_licence')),
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
    # Count licenced sponsors in active jobs too
    active_master['licenced_sponsors'] = sum(1 for j in active if j.get('sponsor_licence'))
    with open(JOBS_FILE, 'w') as f:
        json.dump(active_master, f, indent=2)
    
    print(f"  Master: {master['total']} total jobs ({master['total_active']} active)")
    print(f"  Licenced: {master['licenced_sponsors']} | SC-blocked: {tags.get('sc_blocked', 0)}")
    print(f"  Sources: {dict(sources.most_common(5))}")
    print(f"  Snapshots: {daily_dates[0]} → {daily_dates[-1]}")
    
    return master

if __name__ == '__main__':
    rebuild()
