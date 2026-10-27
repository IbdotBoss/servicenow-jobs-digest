#!/usr/bin/env python3
"""
Keep a current copy of the Home Office register of licensed sponsors.

gov.uk publishes the register as a CSV, usually every working day. This downloads the
newest one to data/register/YYYY-MM-DD.csv (gitignored, about 10 MB a copy), checks that
it looks like the register before trusting it, and keeps the last few copies.

Everything that reads the register calls current(). A failed download never stops the
pipeline: current() falls back to the newest copy on disk, and main() says how old it is.

Run: python3 scripts/sponsor_register.py
"""
import csv
import glob
import os
import re
import sys
import urllib.request
from datetime import date

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REGISTER_DIR = os.path.join(REPO, "data", "register")
PAGE = "https://www.gov.uk/government/publications/register-of-licensed-sponsors-workers"
# The copy used before refreshes existed. Only read if data/register/ is empty.
LEGACY = os.path.expanduser("~/hermes-workspace/Faajaa-Share/2026-05-06_-_Worker_and_Temporary_Worker.csv")
KEEP = 3
MIN_ROWS = 50_000  # the register has well over 100,000 rows; a short file is an error page or a truncation
STALE_DAYS = 7
UA = "Mozilla/5.0 (compatible; servicenow-jobs-digest; +https://github.com/IbdotBoss/servicenow-jobs-digest)"
DATED = re.compile(r"(\d{4}-\d{2}-\d{2})")
REQUIRED = {"Organisation Name", "Route", "Type & Rating"}


def copies():
    return sorted(glob.glob(os.path.join(REGISTER_DIR, "????-??-??.csv")))


def current():
    """Path of the newest register copy, or the legacy copy if none has been downloaded."""
    found = copies()
    return found[-1] if found else LEGACY


def date_of(path):
    m = DATED.search(os.path.basename(path or ""))
    return m.group(1) if m else ""


def looks_like_register(path):
    with open(path, encoding="utf-8-sig", newline="") as f:
        reader = csv.DictReader(f)
        if not REQUIRED <= set(reader.fieldnames or []):
            return False
        return sum(1 for _ in reader) >= MIN_ROWS


def latest_link(page_html):
    """(date, url) of the newest dated CSV linked from the gov.uk page, or (None, None)."""
    links = re.findall(r"https://assets\.publishing\.service\.gov\.uk/[^\"'\s]+\.csv", page_html)
    dated = sorted({(date_of(u), u) for u in links if date_of(u)})
    return dated[-1] if dated else (None, None)


def _get(url, timeout):
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read()


def refresh():
    os.makedirs(REGISTER_DIR, exist_ok=True)
    day, url = latest_link(_get(PAGE, 60).decode("utf-8", "replace"))
    if not url:
        raise RuntimeError("no dated register CSV linked from " + PAGE)
    dest = os.path.join(REGISTER_DIR, f"{day}.csv")
    if os.path.exists(dest):
        return day, "already current"
    part = dest + ".part"
    with open(part, "wb") as f:
        f.write(_get(url, 180))
    if not looks_like_register(part):
        os.remove(part)
        raise RuntimeError(f"the {day} download doesn't look like the register")
    os.replace(part, dest)
    for old in copies()[:-KEEP]:
        os.remove(old)
    return day, "downloaded"


def main():
    try:
        day, status = refresh()
        print(f"Register {day}: {status}")
    except Exception as e:  # network, gov.uk layout change, bad file: keep going on the copy we have
        print(f"⚠️ Register download failed ({e}). Using the {date_of(current()) or 'undated'} copy.")
    used = date_of(current())
    age = (date.today() - date.fromisoformat(used)).days if used else None
    if age is None or age > STALE_DAYS:
        print(f"⚠️ The register copy in use is {age if age is not None else 'of unknown'} days old ({used or 'no date'}). "
              "Employers licensed since then show as no match.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
