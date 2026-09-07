#!/usr/bin/env python3
"""Quick state checker for the ServiceNow jobs pipeline."""
import json
from datetime import datetime

TODAY = datetime.now().strftime("%Y-%m-%d")
MP = "docs/data/master.json"

with open(MP) as f:
    d = json.load(f)

today_jobs = [j for j in d["jobs"] if j.get("last_seen", "")[:10] == TODAY]
active = [j for j in d["jobs"] if j.get("status") == "active"]

print(f"Date: {TODAY}")
print(f"master.json: total={d['total']}, total_active={d['total_active']}, licenced_sponsors={d['licenced_sponsors']}")
print(f"Today's new jobs: {len(today_jobs)}")
print(f"Active jobs: {len(active)}")

dead_sources = ["ComputerJobs", "Totaljobs", "CV-Library", "Deerfoot", "Reed"]
for ds in dead_sources:
    cnt = sum(1 for j in active if ds in str(j.get("sources", [])))
    if cnt:
        print(f"  WARNING: {ds} has {cnt} active jobs!")

sc = sum(1 for j in active if j.get("visa_sponsorship") == "sc_blocked")
lic = sum(1 for j in active if j.get("sponsor_licence") is True)
unavail = sum(1 for j in active if j.get("visa_sponsorship") == "unavailable")
agency = sum(1 for j in active if j.get("visa_sponsorship") == "agency_unknown")
unknown = sum(1 for j in active if j.get("visa_sponsorship") == "unknown")
print(f"  SC-blocked: {sc} | Unavailable: {unavail} | Agency: {agency} | Unknown: {unknown} | Licenced: {lic}")

# Check today's snapshot specifically
daily_path = f"docs/data/daily/jobs_{TODAY}.json"
try:
    with open(daily_path) as f:
        snap = json.load(f)
    print(f"\nDaily snapshot ({TODAY}): {snap.get('total', '?')} jobs")
    print(f"  Sources: {snap.get('sources', {})}")
    snap_jobs = snap.get("jobs", [])
    snap_sc = sum(1 for j in snap_jobs if j.get("visa_sponsorship") == "sc_blocked")
    snap_lic = sum(1 for j in snap_jobs if j.get("sponsor_licence") is True)
    snap_unavail = sum(1 for j in snap_jobs if j.get("visa_sponsorship") == "unavailable")
    print(f"  SC-blocked: {snap_sc} | Unavailable: {snap_unavail} | Licenced: {snap_lic}")
except FileNotFoundError:
    print(f"  Daily snapshot ({TODAY}): NOT FOUND")
