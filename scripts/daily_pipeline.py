#!/usr/bin/env python3
"""
ServiceNow Jobs Digest — Daily Pipeline Orchestrator (v4.5)

Runs the full daily pipeline:
  1. Five source scrapers (JobServe, LinkedIn, Hunt UK, ServiceNow Careers, Nelson Frank)
  2. merge_snapshot.py — merge all source JSONs into daily snapshot
  3. scan_sponsorship.py --csv-only (fast: CSV cross-ref on the daily snapshot)
  4. scan_sponsorship.py (full: page-fetch SC/DV text scan on the daily snapshot)
  5. rebuild_master.py — idempotent merge from all daily snapshots
  6. Git commit + push
  7. Force GitHub Pages rebuild

LinkedIn via Bright Data (brightdata_linkedin.py) — replaces dead Brave-cookie source.
If BRIGHT_DATA_API_KEY is missing or the call fails, LinkedIn degrades to 0 (expected).

Usage:
  python3 scripts/daily_pipeline.py            # normal daily run
  python3 scripts/daily_pipeline.py --linkedin  # force LinkedIn via Bright Data
  python3 scripts/daily_pipeline.py --no-linkedin  # skip LinkedIn entirely

Logging: daily_pipeline.log
"""
import json
import os
import subprocess
import sys
import logging
from logging.handlers import RotatingFileHandler
from datetime import datetime

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest")
DATA_DIR = os.path.join(REPO, "docs", "data")
DAILY_DIR = os.path.join(DATA_DIR, "daily")
TODAY = datetime.now().strftime("%Y-%m-%d")

# ── Logging ──────────────────────────────────────────────────────────────────
logger = logging.getLogger("daily_pipeline")
logger.setLevel(logging.INFO)
fh = RotatingFileHandler(
    os.path.join(REPO, "daily_pipeline.log"),
    maxBytes=10 * 1024 * 1024,
    backupCount=5,
)
fh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(fh)
# Also stdout so cron output is visible
sh = logging.StreamHandler(sys.stdout)
sh.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
logger.addHandler(sh)


def log(msg, level="info"):
    """Log to both file and stdout."""
    getattr(logger, level)(msg)
    print(msg, flush=True)


def run_script(script_path, cwd=None, timeout=300, extra_args=None):
    """Run a Python script as a subprocess. Returns (success, stdout, stderr)."""
    cwd = cwd or REPO
    cmd = [sys.executable, script_path]
    if extra_args:
        cmd.extend(extra_args)
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        if result.stdout.strip():
            log(f"  [stdout] {result.stdout.strip()[:500]}")
        if result.returncode != 0:
            log(
                f"  [stderr] {result.stderr.strip()[:500]}",
                level="error" if result.returncode != 0 else "info",
            )
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        log(f"  TIMEOUT after {timeout}s", level="error")
        return False, "", "timeout"
    except Exception as e:
        log(f"  ERROR: {e}", level="error")
        return False, "", str(e)


def run_subprocess(cmd, cwd=None, timeout=120):
    """Run a raw subprocess command (e.g. git, gh). Returns (success, output)."""
    cwd = cwd or REPO
    try:
        result = subprocess.run(
            cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout
        )
        output = result.stdout.strip()
        if result.returncode != 0:
            err = result.stderr.strip()
            if err:
                output += f"\n{err}"
        return result.returncode == 0, output
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


# ── Source scrapers ──────────────────────────────────────────────────────────

SCRAPERS = [
    ("JobServe (mobile SHD)",  "scripts/jobserve_scraper.py"),
    ("Hunt UK (Playwright)",   "scripts/hunt_uk_scraper.py"),
    ("ServiceNow Careers (RSS)", "scripts/servicenow_careers_scraper.py"),
    ("Nelson Frank (Playwright)", "scripts/nelson_frank_scraper.py"),
]


def run_jobserve():
    """JobServe mobile scraper via curl + SHD session."""
    log(">>> Running JobServe scraper...")
    ok, out, err = run_script(os.path.join(REPO, "scripts/jobserve_scraper.py"))
    if ok:
        data = read_json(os.path.join(DATA_DIR, "jobserve_jobs.json"))
        count = len(data) if isinstance(data, list) else 0
        log(f"  ✅ JobServe: {count} jobs")
    else:
        log(f"  ❌ JobServe scraper failed", level="error")
    return ok


def run_hunt_uk():
    """Hunt UK scraper via Playwright (extracts real /job/ URLs)."""
    log(">>> Running Hunt UK scraper...")
    ok, out, err = run_script(os.path.join(REPO, "scripts/hunt_uk_scraper.py"))
    if ok:
        data = read_json(os.path.join(DATA_DIR, "hunt_uk_jobs.json"))
        count = len(data) if isinstance(data, list) else 0
        log(f"  ✅ Hunt UK: {count} jobs")
    else:
        log(f"  ❌ Hunt UK scraper failed", level="error")
    return ok


def run_servicenow_careers():
    """ServiceNow Careers RSS feed — direct employer, guaranteed licence."""
    log(">>> Running ServiceNow Careers RSS scraper...")
    ok, out, err = run_script(os.path.join(REPO, "scripts/servicenow_careers_scraper.py"))
    if ok:
        data = read_json(os.path.join(DATA_DIR, "servicenow_careers_jobs.json"))
        count = len(data) if isinstance(data, list) else 0
        log(f"  ✅ ServiceNow Careers: {count} jobs")
    else:
        log(f"  ❌ ServiceNow Careers scraper failed", level="error")
    return ok


def run_nelson_frank():
    """Nelson Frank via Playwright category sub-pages."""
    log(">>> Running Nelson Frank scraper...")
    ok, out, err = run_script(os.path.join(REPO, "scripts/nelson_frank_scraper.py"))
    if ok:
        data = read_json(os.path.join(DATA_DIR, "nelson_frank_jobs.json"))
        count = len(data) if isinstance(data, list) else 0
        log(f"  ✅ Nelson Frank: {count} jobs")
    else:
        log(f"  ❌ Nelson Frank scraper failed (best-effort, continuing)", level="warn")
    # Nelson Frank is best-effort — don't fail pipeline on error
    return True


def run_linkedin_brightdata():
    """LinkedIn via Bright Data Scraper API — account-free replacement for Brave cookies.

    Uses discover() (async) — triggers a snapshot search for 'ServiceNow' in United Kingdom,
    polls for results, normalizes to the legacy schema.

    Falls back gracefully to 0 jobs if BRIGHT_DATA_API_KEY is missing or the API fails.
    """
    log(">>> Running LinkedIn (Bright Data)...")
    try:
        from brightdata_linkedin import BrightDataLinkedIn
    except ImportError:
        log("  ⚠️ brightdata_linkedin.py not importable — skipping LinkedIn", level="warn")
        write_empty_linkedin_json()
        return True

    api_key = os.environ.get("BRIGHT_DATA_API_KEY")
    if not api_key:
        log("  ⚠️ BRIGHT_DATA_API_KEY not set — skipping LinkedIn", level="warn")
        write_empty_linkedin_json()
        return True

    try:
        bd = BrightDataLinkedIn(api_key=api_key, verbose=False)
        jobs = bd.discover(keyword="ServiceNow", location="United Kingdom")
        # Filter to SN-relevant roles
        sn_kw = ["servicenow", "snow", "itsm", "csm", "itom", "hrsd", "secops",
                 "csam", "grcc", "fsm"]
        filtered = []
        for j in jobs:
            title = (j.get("title", "") or "").lower()
            if any(k in title for k in sn_kw):
                filtered.append(j)

        os.makedirs(DATA_DIR, exist_ok=True)
        out_path = os.path.join(DATA_DIR, "linkedin_jobs.json")
        with open(out_path, "w") as f:
            json.dump(filtered, f, indent=2, ensure_ascii=False)
        log(f"  ✅ LinkedIn (Bright Data): {len(filtered)} jobs")
        return True
    except Exception as e:
        log(f"  ⚠️ Bright Data LinkedIn failed ({e}) — continuing", level="warn")
        write_empty_linkedin_json()
        return True


def write_empty_linkedin_json():
    """Write empty LinkedIn JSON so merge_snapshot doesn't choke on missing file."""
    path = os.path.join(DATA_DIR, "linkedin_jobs.json")
    with open(path, "w") as f:
        json.dump([], f)


# ── Helpers ──────────────────────────────────────────────────────────────────

def read_json(path):
    if not os.path.exists(path):
        return None
    try:
        with open(path) as f:
            return json.load(f)
    except Exception:
        return None


def scan_daily_snapshot(csv_only=True):
    """Run scan_sponsorship.py against today's daily snapshot file."""
    daily_file = os.path.join(DAILY_DIR, f"jobs_{TODAY}.json")
    if not os.path.exists(daily_file):
        log(f"  ⚠️ No daily snapshot for {TODAY} — skipping scan", level="warn")
        return True

    flag = "--csv-only" if csv_only else ""
    args = ["--file", daily_file, "--skip-defaults"]
    if csv_only:
        args.insert(0, "--csv-only")

    log(f">>> scan_sponsorship.py ({'csv-only' if csv_only else 'full page-fetch'}) on {TODAY} snapshot...")
    ok, out, err = run_script(
        os.path.join(REPO, "scripts/scan_sponsorship.py"),
        cwd=REPO,
        timeout=600,
        extra_args=args,
    )
    if ok:
        # Reload the scanned file to report counts
        data = read_json(daily_file)
        if isinstance(data, dict):
            jobs = data.get("jobs", [])
        elif isinstance(data, list):
            jobs = data
        else:
            jobs = []
        from collections import Counter
        tags = Counter(j.get("visa_sponsorship", "unknown") for j in jobs)
        licenced = sum(1 for j in jobs if j.get("sponsor_licence"))
        label = "CSV-only" if csv_only else "full"
        log(f"  ✅ Scan ({label}): {len(jobs)} jobs | tags: {dict(tags)} | licenced: {licenced}")
    else:
        log(f"  ❌ scan_sponsorship.py ({'csv-only' if csv_only else 'full'}) failed", level="error")
    return ok


def rebuild_master():
    """Run rebuild_master.py to merge all daily snapshots into master.json + jobs.json."""
    log(">>> Running rebuild_master.py...")
    ok, out, err = run_script(
        os.path.join(REPO, "scripts/rebuild_master.py"),
        cwd=REPO,
        timeout=120,
    )
    if ok:
        master = read_json(os.path.join(DATA_DIR, "master.json"))
        if master:
            log(f"  ✅ Master: {master['total']} total | {master['total_active']} active | "
                f"{master['licenced_sponsors']} licenced | snapshots: {len(master.get('daily_snapshots', []))}")
    else:
        log("  ❌ rebuild_master.py failed", level="error")
    return ok


def git_commit_push():
    """Stage data files, commit, and push to GitHub."""
    log(">>> Git commit & push...")
    # Only stage our data files + logs that matter
    ok1, out1 = run_subprocess(
        ["git", "add", "docs/data/"],
        timeout=30,
    )
    if not ok1:
        log(f"  ⚠️ git add: {out1}", level="warn")

    # Check if there's anything to commit
    ok2, out2 = run_subprocess(
        ["git", "status", "--porcelain"],
        timeout=30,
    )
    if not out2.strip():
        log("  ℹ️ Nothing to commit (working tree clean)")
        return True

    commit_msg = f"Daily update {TODAY}"
    ok3, out3 = run_subprocess(
        ["git", "commit", "-m", commit_msg],
        timeout=30,
    )
    if not ok3:
        if "nothing to commit" in out3:
            log("  ℹ️ Nothing to commit")
            return True
        log(f"  ❌ git commit failed: {out3}", level="error")
        return False

    ok4, out4 = run_subprocess(
        ["git", "push", "origin", "main"],
        timeout=60,
    )
    if ok4:
        log("  ✅ Pushed to GitHub")
    else:
        log(f"  ❌ git push failed: {out4}", level="error")
        return False
    return True


def force_pages_rebuild():
    """Force a GitHub Pages build to bust CDN cache."""
    log(">>> Forcing GitHub Pages rebuild...")
    ok, out = run_subprocess(
        ["gh", "api", "-X", "POST",
         f"repos/IbdotBoss/servicenow-jobs-digest/pages/builds"],
        timeout=30,
    )
    if ok:
        log("  ✅ Pages rebuild triggered")
    else:
        log(f"  ⚠️ Pages rebuild failed (may need manual trigger): {out[:200]}", level="warn")
    return ok


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    skip_linkedin = "--no-linkedin" in sys.argv
    force_linkedin = "--linkedin" in sys.argv

    log("=" * 70)
    log("DAILY SERVICE NOW JOBS DIGEST — FULL PIPELINE")
    log("=" * 70)
    log(f"Date: {TODAY}")

    errors = []

    # ── Step 1: Run scrapers ──────────────────────────────────────────────
    log("\n" + "─" * 70)
    log("STEP 1: Source scrapers")
    log("─" * 70)

    run_jobserve()

    if force_linkedin:
        run_linkedin_brightdata()
    elif not skip_linkedin:
        run_linkedin_brightdata()

    run_hunt_uk()
    run_servicenow_careers()
    run_nelson_frank()

    # ── Step 2: Merge into daily snapshot ─────────────────────────────────
    log("\n" + "─" * 70)
    log("STEP 2: Merge daily snapshot")
    log("─" * 70)
    ok, out, err = run_script(
        os.path.join(REPO, "scripts/merge_snapshot.py"),
        cwd=REPO,
        timeout=60,
    )
    if ok:
        daily = read_json(os.path.join(DAILY_DIR, f"jobs_{TODAY}.json"))
        if daily:
            log(f"  ✅ Snapshot: {daily['total']} unique jobs | sources: {daily.get('sources', {})}")
    else:
        errors.append("merge_snapshot failed")

    # ── Step 3: Scan sponsorship (csv-only) ───────────────────────────────
    log("\n" + "─" * 70)
    log("STEP 3: Sponsorship scan (csv-only)")
    log("─" * 70)
    scan_daily_snapshot(csv_only=True)

    # ── Step 4: Scan sponsorship (full page-fetch) ────────────────────────
    log("\n" + "─" * 70)
    log("STEP 4: Sponsorship scan (full page-fetch for SC/DV)")
    log("─" * 70)
    scan_daily_snapshot(csv_only=False)

    # ── Step 5: Rebuild master ────────────────────────────────────────────
    log("\n" + "─" * 70)
    log("STEP 5: Rebuild master")
    log("─" * 70)
    rebuild_master()

    # ── Step 6: Git commit & push ─────────────────────────────────────────
    log("\n" + "─" * 70)
    log("STEP 6: Git commit & push")
    log("─" * 70)
    git_commit_push()

    # ── Step 7: Force Pages rebuild ───────────────────────────────────────
    log("\n" + "─" * 70)
    log("STEP 7: Force GitHub Pages rebuild")
    log("─" * 70)
    force_pages_rebuild()

    # ── Summary ───────────────────────────────────────────────────────────
    log("\n" + "=" * 70)
    log("DAILY PIPELINE COMPLETED")
    log("=" * 70)

    # Final verification
    master = read_json(os.path.join(DATA_DIR, "master.json"))
    if master:
        tags = {}
        for j in master.get("jobs", []):
            t = j.get("visa_sponsorship", "unknown")
            tags[t] = tags.get(t, 0) + 1
        log(f"\n📊 FINAL STATE:")
        log(f"  Live: https://ibdotboss.github.io/servicenow-jobs-digest/")
        log(f"  Data: https://ibdotboss.github.io/servicenow-jobs-digest/data/master.json")
        log(f"  Total: {master['total']} | Active: {master['total_active']} | Licenced: {master['licenced_sponsors']}")
        log(f"  Tags: {tags}")
        log(f"  Snapshots: {len(master.get('daily_snapshots', []))}")
        log(f"  Sources: {master.get('sources', {})}")

    if errors:
        log(f"\n⚠️ Errors during pipeline: {errors}", level="warn")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
