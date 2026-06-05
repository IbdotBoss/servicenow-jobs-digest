#!/usr/bin/env python3
import json, os
from datetime import datetime

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
DAILY_DIR = os.path.join(REPO, "daily")
TODAY = datetime.now().strftime("%Y-%m-%d")

SOURCE_FILES = {
    "JobServe": os.path.join(REPO, "jobserve_jobs.json"),
    "LinkedIn": os.path.join(REPO, "linkedin_jobs.json"),
    "Hunt UK": os.path.join(REPO, "hunt_uk_jobs.json"),
    "ServiceNow Careers": os.path.join(REPO, "sn_careers_jobs.json"),
    "Nelson Frank": os.path.join(REPO, "nelson_frank_jobs.json"),
}


def read_json(path):
    if not os.path.exists(path):
        print(f"[WARN] Missing file: {path}")
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception as e:
        print(f"[WARN] Could not read {path}: {e}")
        return None


def normalize(job, default_source):
    job.setdefault("source", default_source)
    job.setdefault("sn_role", job.get("sn_role", False))
    job.setdefault("role_type", job.get("role_type", "other"))
    job.setdefault("remote", job.get("remote", "onsite"))
    job.setdefault("employment", job.get("employment", "permanent"))
    job.setdefault("sc_clearance", job.get("sc_clearance", False))
    job.setdefault("grad_scheme", job.get("grad_scheme", False))
    job.setdefault("link_status", job.get("link_status", "live"))
    job.setdefault("visa_sponsorship", job.get("visa_sponsorship", "unknown"))
    job.setdefault("sponsor_licence", job.get("sponsor_licence", False))
    job.setdefault("sponsorship_mentioned", job.get("sponsorship_mentioned", False))
    job.setdefault("description", job.get("description", ""))
    if not job.get("date_posted"):
        job["date_posted"] = TODAY
    if not job.get("scraped_at"):
        job["scraped_at"] = TODAY
    return job


def main():
    os.makedirs(DAILY_DIR, exist_ok=True)

    all_jobs = []
    sources_counter = {}
    for src_name, path in SOURCE_FILES.items():
        data = read_json(path)
        if not data:
            continue
        if isinstance(data, dict):
            jobs = data.get("jobs", [])
        elif isinstance(data, list):
            jobs = data
        else:
            print(f"[WARN] Unexpected format in {src_name}, skipping")
            continue

        before = len(all_jobs)
        for j in jobs:
            all_jobs.append(normalize(j, src_name))
        added = len(all_jobs) - before
        sources_counter[src_name] = added
        print(f"{src_name}: {added} jobs")

    seen = set()
    unique_jobs = []
    for j in all_jobs:
        key = (j.get("title", "").lower().strip(), j.get("company", "").lower().strip())
        if key in seen:
            continue
        seen.add(key)
        unique_jobs.append(j)
    print(f"Total unique after dedup: {len(unique_jobs)}")

    snapshot = {
        "updated": TODAY,
        "date": TODAY,
        "total": len(unique_jobs),
        "sources": sources_counter,
        "jobs": unique_jobs,
    }

    daily_path = os.path.join(DAILY_DIR, f"jobs_{TODAY}.json")
    with open(daily_path, "w") as f:
        json.dump(snapshot, f, indent=2)
    print(f"Daily snapshot written: {daily_path}")

    jobs_json_path = os.path.join(REPO, "jobs.json")
    with open(jobs_json_path, "w") as f:
        json.dump({"jobs": unique_jobs, "total": len(unique_jobs)}, f, indent=2)
    print(f"jobs.json updated: {jobs_json_path}")


if __name__ == "__main__":
    main()
