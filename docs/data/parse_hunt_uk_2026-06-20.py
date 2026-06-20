#!/usr/bin/env python3
"""Minimal Hunt UK ingest from the latest web_extract summary.

This parser is intentionally lightweight for the 2026-06-20 cached extract.
It normalizes postings into a job dict compatible with build_daily_snapshot.py.
"""

import json
import os
import re
from datetime import datetime

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest/docs/data")
TODAY = datetime.now().strftime("%Y-%m-%d")

EXTRACT_PATH = os.path.join(REPO, "hunt_uk_extract_2026-06-20.json")


def load_extract():
    with open(EXTRACT_PATH) as f:
        return json.load(f)


def jobs_from_summary():
    data = load_extract()
    results = data.get("results", [])
    if not results:
        return []
    summary = results[0].get("content", "")
    blocks = re.split(r"\n---\n\n", summary)
    jobs = []
    current = {}
    for block in blocks:
        lines = block.splitlines()
        title = None
        company = None
        location = None
        pay = ""
        role_type = "Permanent"
        posting_date = None
        for line in lines:
            s = line.strip()
            if s.startswith("### "):
                title = s[4:].strip()
            elif s.startswith("- **Employer**: "):
                company = s[len("- **Employer**: "):].strip()
            elif s.startswith("- **Location**: "):
                location = s[len("- **Location**: "):].strip()
            elif s.startswith("- **Posting Date**: "):
                raw = s[len("- **Posting Date**: "):].strip()
                # Hunt UK returns m/d/YYYY format
                m = re.match(r"(\d{1,2})/(\d{1,2})/(\d{4})", raw)
                if m:
                    month, day, year = m.groups()
                    posting_date = f"{year}-{int(month):02d}-{int(day):02d}"
            elif s.startswith("- **Pay Rate**: "):
                pay = s[len("- **Pay Rate**: "):].strip()
            elif s.startswith("- **Pay**: "):
                pay = s[len("- **Pay**: "):].strip()
            elif "Contract" in s:
                role_type = "Contract"
        if title and company:
            if not posting_date:
                posting_date = TODAY
            if not location:
                location = "United Kingdom"
            title_clean = re.sub(r"\s+\|\s+\d+ openings?.*$", "", title)
            if role_type == "Contract" and pay:
                salary_display = pay
            else:
                salary_display = "Not listed"
            jobs.append({
                "title": title_clean,
                "company": company,
                "location": location,
                "url": "https://huntukvisasponsors.com/jobs?q=servicenow",
                "date_posted": posting_date,
                "visa_sponsorship": "unknown",
                "source": "Hunt UK",
                "salary_display": salary_display,
                "role_type": role_type,
                "description": "",
                "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            })
    return jobs


def main():
    jobs = jobs_from_summary()
    print(f"Hunt UK parsed jobs: {len(jobs)}")
    for j in jobs:
        print(
            f"- {j['title']} | {j['company']} | {j['location']} | {j['date_posted']}"
        )
    out_path = os.path.join(REPO, "hunt_uk_jobs.json")
    with open(out_path, "w") as f:
        json.dump(jobs, f, indent=2)
    print(f"Saved: {out_path}")


if __name__ == "__main__":
    main()
