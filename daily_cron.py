#!/usr/bin/env python3
"""
Daily cron job for ServiceNow Jobs Digest (v4.5)

Delegates to scripts/daily_pipeline.py which runs the full pipeline:
  5 source scrapers → merge_snapshot → scan_sponsorship (csv-only + full) →
  rebuild_master → git push → GitHub Pages rebuild
"""
import subprocess
import sys
import os

REPO = os.path.expanduser("~/hermes-workspace/servicenow-jobs-digest")

def main():
    print("=" * 60)
    print("DAILY SERVICE NOW JOBS DIGEST — CRON JOB")
    print("=" * 60)
    print(f"Time: {__import__('datetime').datetime.now()}")

    # Delegate to the full pipeline orchestrator
    result = subprocess.run(
        [sys.executable, os.path.join(REPO, "scripts/daily_pipeline.py")],
        cwd=REPO,
        capture_output=True,
        text=True,
        timeout=1800,  # 30 min hard cap
    )

    # Stream output
    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr, file=sys.stderr)

    print("=" * 60)
    if result.returncode == 0:
        print("CRON JOB COMPLETED SUCCESSFULLY")
    else:
        print(f"CRON JOB FAILED (exit code {result.returncode})")
    print("=" * 60)

    sys.exit(result.returncode)

if __name__ == "__main__":
    main()
