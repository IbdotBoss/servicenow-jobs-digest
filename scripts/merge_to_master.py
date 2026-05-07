#!/usr/bin/env python3
"""
Master archive merge script.
Takes today's scrape snapshot and merges into the master archive.
Tracks first_seen, last_seen, and status per job.

Usage: python3 scripts/merge_to_master.py [--snapshot docs/data/today.json]
"""

import json, sys, os, shutil
from datetime import datetime, timedelta
from pathlib import Path

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
MASTER_FILE = os.path.join(REPO, "master.json")
SNAPSHOT_FILE = os.path.join(REPO, "jobs.json")  # today's scrape
DAILY_DIR = os.path.join(REPO, "daily")  # archive of daily snapshots

TODAY = datetime.now().strftime("%Y-%m-%d")
STALE_DAYS = 7
EXPIRED_DAYS = 30

def job_key(job):
    """Unique key for dedup: normalized title + company"""
    title = job.get('title', '').lower().strip()
    company = job.get('company', '').lower().strip()
    # Normalize: strip agency suffixes
    for suffix in [' - the servicenow customer workflow experts', ' (agency)', ' via hays', ' via sthree']:
        company = company.replace(suffix, '')
    return f"{title}|{company}"

def load_master():
    if os.path.exists(MASTER_FILE):
        with open(MASTER_FILE) as f:
            return json.load(f)
    return {
        "updated": TODAY,
        "total": 0,
        "total_active": 0,
        "verified": 0,
        "sc_blocked": 0,
        "sources": {},
        "daily_snapshots": [],
        "jobs": []
    }

def load_snapshot():
    if os.path.exists(SNAPSHOT_FILE):
        with open(SNAPSHOT_FILE) as f:
            return json.load(f)
    return {"jobs": []}

def save_daily_snapshot(snapshot):
    """Archive today's raw scrape"""
    os.makedirs(DAILY_DIR, exist_ok=True)
    daily_file = os.path.join(DAILY_DIR, f"jobs_{TODAY}.json")
    snapshot['date'] = TODAY
    with open(daily_file, 'w') as f:
        json.dump(snapshot, f, indent=2)
    print(f"  Saved daily snapshot: {daily_file}")

def status_from_dates(first_seen, last_seen):
    """Determine job status based on dates"""
    last = datetime.strptime(last_seen, "%Y-%m-%d")
    age = (datetime.now() - last).days
    
    if age > EXPIRED_DAYS:
        return "expired"
    elif age > STALE_DAYS:
        return "stale"
    return "active"

def merge(snapshot=None):
    """Merge today's scrape into master archive"""
    if snapshot is None:
        snapshot = load_snapshot()
    
    master = load_master()
    master_jobs = master['jobs']
    today_jobs = snapshot.get('jobs', [])
    
    # Build index of existing jobs by key
    existing = {}
    for j in master_jobs:
        existing[job_key(j)] = j
    
    # Save daily snapshot
    save_daily_snapshot(snapshot)
    
    # Merge: update existing, add new
    new_count = 0
    updated_count = 0
    today_keys = set()
    
    for j in today_jobs:
        key = job_key(j)
        today_keys.add(key)
        
        if key in existing:
            # Update existing job
            old = existing[key]
            old['last_seen'] = TODAY
            
            # Update mutable fields (salary, location, url might change)
            for field in ['salary_display', 'salary_min', 'salary_max', 'url', 'location']:
                if j.get(field) and j[field] != old.get(field):
                    old[field] = j[field]
            
            # Update status
            old['status'] = status_from_dates(old.get('first_seen', TODAY), TODAY)
            
            # Update sponsorship if new scan is better
            if j.get('visa_sponsorship') not in ('unknown', 'agency_unknown'):
                old['visa_sponsorship'] = j['visa_sponsorship']
            
            # Update source if new
            if j.get('source') and j['source'] not in old.get('sources', [old.get('source', '')]):
                old.setdefault('sources', [old.get('source', '')])
                if j['source'] not in old['sources']:
                    old['sources'].append(j['source'])
            
            updated_count += 1
        else:
            # New job
            j['first_seen'] = TODAY
            j['last_seen'] = TODAY
            j['status'] = 'active'
            j.setdefault('sources', [j.get('source', 'unknown')])
            master_jobs.append(j)
            new_count += 1
    
    # Mark jobs NOT seen today as stale/expired
    for j in master_jobs:
        key = job_key(j)
        if key not in today_keys:
            j['status'] = status_from_dates(
                j.get('first_seen', j.get('last_seen', TODAY)),
                j.get('last_seen', TODAY)
            )
    
    # Update metadata
    master['updated'] = TODAY
    master['total'] = len(master_jobs)
    master['total_active'] = sum(1 for j in master_jobs if j['status'] == 'active')
    
    # Recount stats
    from collections import Counter
    tags = Counter(j.get('visa_sponsorship', 'unknown') for j in master_jobs)
    master['verified'] = tags.get('sponsor_verified', 0) + tags.get('verified', 0)
    master['sc_blocked'] = tags.get('sc_blocked', 0)
    
    # Update source counts
    sources = Counter()
    for j in master_jobs:
        srcs = j.get('sources', [j.get('source', 'unknown')])
        for s in srcs:
            sources[s] += 1
    master['sources'] = dict(sources.most_common(20))
    
    # Track daily snapshots
    if TODAY not in master.get('daily_snapshots', []):
        master.setdefault('daily_snapshots', []).append(TODAY)
    
    # Save master
    with open(MASTER_FILE, 'w') as f:
        json.dump(master, f, indent=2)
    
    # Also copy to jobs.json for backward compatibility with index page
    shutil.copy(MASTER_FILE, SNAPSHOT_FILE)
    
    print(f"\n  MASTER ARCHIVE: {master['total']} total jobs")
    print(f"  Active: {master['total_active']} | New today: {new_count} | Updated: {updated_count}")
    print(f"  Sponsors: {master['verified']} | SC-blocked: {master['sc_blocked']}")
    
    return master

if __name__ == '__main__':
    snapshot_path = sys.argv[2] if len(sys.argv) > 2 and sys.argv[1] == '--snapshot' else None
    if snapshot_path:
        with open(snapshot_path) as f:
            snapshot = json.load(f)
        merge(snapshot)
    else:
        merge()
