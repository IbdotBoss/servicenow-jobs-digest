#!/usr/bin/env python3
"""
Export the files the public page reads, from master.json.

  docs/data/active.json            open roles only, slim fields, display-clean text (~60 KB)
  docs/data/archive/YYYY-MM.json   stale and expired roles, by the month they were last seen
  docs/data/archive/index.json     the list of archive months

master.json stays the record and keeps every raw value. Cleaning here is presentation
only: casing, separators, placeholders. It never changes what a listing says.

Run after rebuild_master.py (daily_pipeline.py step 5b).
"""
import json
import os
import re
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(REPO, "docs", "data")
MASTER_FILE = os.path.join(DATA_DIR, "master.json")
ACTIVE_FILE = os.path.join(DATA_DIR, "active.json")
ARCHIVE_DIR = os.path.join(DATA_DIR, "archive")

SOURCE_NAMES = {"hunt_uk": "Hunt UK"}
# In an all-caps company name, words of four letters or fewer are usually acronyms (EPAM, KPMG, UK), except these.
SHORT_WORDS = {"LTD": "Ltd", "INC": "Inc", "CO": "Co"}


def _squash(s):
    return re.sub(r"\s+", " ", s or "").strip()


def clean_title(title):
    t = _squash(title)
    t = re.sub(r"\bservice\s?now\b", "ServiceNow", t, flags=re.IGNORECASE)
    t = re.sub(r"\s*\|\s*", " | ", t)
    t = t.strip(" |-–—")
    # Shouted words of five or more letters read as typing, not as acronyms (OUTSIDE, not ITSM).
    t = re.sub(r"\b[A-Z]{5,}\b", lambda m: m.group(0).capitalize(), t)
    if t and t[0].islower():
        t = t[0].upper() + t[1:]
    return t


def clean_company(company):
    c = _squash(company)
    if c.lower() == "[view listing]":
        return ""
    letters = re.sub(r"[^A-Za-z]", "", c)
    if len(letters) > 4 and letters.isupper():
        c = " ".join(w.capitalize() if len(w) >= 5 else SHORT_WORDS.get(w, w) for w in c.split(" "))
    return c


def sponsor_status(job):
    v = job.get("visa_sponsorship")
    if v == "sc_blocked":
        return "clearance"
    if v == "unavailable":
        return "no"
    if v == "agency_unknown":
        return "agency"
    return "licensed" if job.get("sponsor_licence") else "unknown"


def slim(job):
    sp = sponsor_status(job)
    salary = _squash(job.get("salary_display"))
    remote = job.get("remote")
    return {
        "t": clean_title(job.get("title")),
        "c": clean_company(job.get("company")),
        "l": _squash(job.get("location")),
        # The scrapers default to "onsite" when they can't tell, so only a positive signal is shown.
        "r": remote if remote in ("remote", "hybrid") else None,
        "s": "" if salary == "Not listed" else salary,
        "u": job.get("url") or "",
        "src": SOURCE_NAMES.get(job.get("source"), job.get("source") or ""),
        "role": job.get("role_type") or "other",
        "sp": sp,
        # Older scans set this flag on pages that refuse sponsorship; never show it beside a refusal.
        "m": bool(job.get("sponsorship_mentioned")) and sp in ("licensed", "unknown"),
        "g": bool(job.get("grad_scheme")),
        "fs": job.get("first_seen") or "",
        "ls": job.get("last_seen") or "",
        "p": (job.get("date_posted") or "")[:10],
    }


def split(jobs):
    active, archive = [], defaultdict(list)
    for j in jobs:
        if j.get("status") == "active":
            active.append(j)
        else:
            archive[(j.get("last_seen") or "unknown")[:7]].append(j)
    return active, dict(archive)


def _write(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, separators=(",", ":"))


def main():
    with open(MASTER_FILE, encoding="utf-8") as f:
        master = json.load(f)
    active, archive = split(master.get("jobs", []))
    updated = master.get("updated", "")
    _write(ACTIVE_FILE, {"updated": updated, "jobs": [slim(j) for j in active]})
    for month, jobs in archive.items():
        _write(os.path.join(ARCHIVE_DIR, f"{month}.json"),
               {"month": month, "jobs": [dict(slim(j), status=j.get("status")) for j in jobs]})
    _write(os.path.join(ARCHIVE_DIR, "index.json"),
           {"updated": updated, "months": [{"month": m, "count": len(archive[m])} for m in sorted(archive, reverse=True)]})
    print(f"active.json: {len(active)} roles, {os.path.getsize(ACTIVE_FILE) // 1024} KB | archive: {len(archive)} months, "
          f"{sum(len(v) for v in archive.values())} roles")


if __name__ == "__main__":
    main()
