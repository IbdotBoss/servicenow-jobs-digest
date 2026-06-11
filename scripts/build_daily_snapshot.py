#!/usr/bin/env python3
"""Merge source files into today's daily snapshot."""
import json, os
from datetime import datetime

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
DAILY_DIR = os.path.join(REPO, "daily")
TODAY = datetime.now().strftime("%Y-%m-%d")
TODAY_DT = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

os.makedirs(DAILY_DIR, exist_ok=True)


def load_json(path):
    if not os.path.exists(path):
        return []
    with open(path) as f:
        data = json.load(f)
    if isinstance(data, dict):
        if "jobs" in data and isinstance(data["jobs"], list):
            return data["jobs"]
        if "results" in data:
            return data["results"]
        return []
    if isinstance(data, list):
        return data
    return []


all_jobs = []
source_counts = {}

for label, filename in [
    ("JobServe", "jobserve_jobs.json"),
    ("LinkedIn", "linkedin_jobs.json"),
    ("ServiceNow Careers", "servicenow_careers_jobs.json"),
    ("Nelson Frank", "nelson_frank_jobs.json"),
    ("Hunt UK", "hunt_uk_jobs.json"),
    # Reed is decommissioned: no longer loaded into daily snapshots
]:
    path = os.path.join(REPO, filename)
    jobs = load_json(path)
    for j in jobs:
        j.setdefault("source", label)
        j.setdefault("source_type", "aggregator")
        j.setdefault("date_posted", j.get("date_posted", TODAY))
        j.setdefault("visa_sponsorship", "unknown")
        j.setdefault("salary_display", "Not listed")
        j.setdefault("role_type", "unknown")
        j.setdefault("remote", "unknown")
        j.setdefault("employment", "unknown")
        j.setdefault("sc_clearance", False)
        j.setdefault("grad_scheme", False)
        j.setdefault("link_status", "live")
        j.setdefault("description", "")
        j.setdefault("scraped_at", TODAY_DT)
    all_jobs.extend(jobs)
    source_counts[label] = len(jobs)
    print(f"{label}: {len(jobs)} jobs")

tags = {}
for j in all_jobs:
    tags[j.get("visa_sponsorship", "unknown")] = tags.get(j.get("visa_sponsorship", "unknown"), 0) + 1

snapshot = {
    "updated": TODAY,
    "updated_at": TODAY_DT,
    "total": len(all_jobs),
    "sources": source_counts,
    "jobs": all_jobs,
}

today_file = os.path.join(DAILY_DIR, f"jobs_{TODAY}.json")
with open(today_file, "w") as f:
    json.dump(snapshot, f, indent=2)

print(f"\\n✅ Daily snapshot saved: {today_file}")
print(f"   Total: {snapshot['total']} jobs")
print(f"   Sources: {source_counts}")
print(f"   Unknown: {tags.get('unknown', 0)} | agency_unknown: {tags.get('agency_unknown', 0)} | SC-blocked pre-scan: {tags.get('sc_blocked', 0)}")
