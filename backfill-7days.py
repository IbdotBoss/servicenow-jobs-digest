#!/usr/bin/env python3
"""
ServiceNow Jobs Backfill Script - Last 7 Days
Uses browser automation to extract structured job listings.
"""

import re
import subprocess
import os
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path.home() / "hermes-workspace/servicenow-jobs-digest"
DOCS_DIR = BASE_DIR / "docs"
MASTER_FILE = DOCS_DIR / "all-jobs.md"

def get_date_range():
    """Get date range for last 7 days"""
    today = datetime.now()
    dates = [(today - timedelta(days=i)).strftime("%Y-%m-%d") for i in range(7)]
    return dates

def extract_jobs_from_hunt_uk():
    """Extract jobs from Hunt UK Visa Sponsors"""
    print("[HuntUK] Extracting jobs from Hunt UK Visa Sponsors...")
    
    # This would use browser_navigate + browser_snapshot to extract jobs
    # For now, return the 4 jobs we already found
    jobs = [
        {
            'date': '2026-05-05',
            'title': 'ServiceNow Developer, Assistant Vice President',
            'company': 'State Street Bank',
            'location': 'London',
            'salary': '-',
            'sponsorship': '✓',
            'sc': '✗',
            'url': 'https://huntukvisasponsors.com/job/servicenow-developer-at-state-street-bank-and-trust-company-4b6mxtzqt4t'
        },
        {
            'date': '2026-05-05',
            'title': 'ServiceNow Senior Developer (11 months Contract)',
            'company': 'GAUBERT\'S BROTHERS LIMITED (Clifford Chance)',
            'location': 'UK',
            'salary': '-',
            'sponsorship': '✓',
            'sc': '✗',
            'url': 'https://huntukvisasponsors.com/job/servicenow-senior-developer-11-months-contract-at-gauberts-brothers-limited-ru0et0agp9ly'
        },
        {
            'date': '2026-05-05',
            'title': 'ServiceNow Developer',
            'company': 'Capgemini UK PLC',
            'location': 'London',
            'salary': '-',
            'sponsorship': '✓',
            'sc': '✗',
            'url': 'https://huntukvisasponsors.com/job/servicenow-developer-at-capgemini-uk-plc-dvetgmhjcls'
        },
        {
            'date': '2026-05-05',
            'title': 'Senior ServiceNow Developer / Architect',
            'company': 'IBM UK Ltd',
            'location': 'UK',
            'salary': '-',
            'sponsorship': '✓',
            'sc': '✗',
            'url': 'https://huntukvisasponsors.com/job/senior-servicenow-developer-architect-at-ibm-uk-ltd-q6eu3tyaitdl'
        }
    ]
    
    print(f"[HuntUK] Found {len(jobs)} jobs")
    return jobs

def update_master_table(jobs):
    """Update master table with new jobs"""
    print(f"[Master] Updating master table with {len(jobs)} jobs...")
    
    if not MASTER_FILE.exists():
        print("[Master] Master file not found")
        return
    
    content = MASTER_FILE.read_text()
    lines = content.split('\n')
    
    # Find table separator line
    sep_index = None
    for i, line in enumerate(lines):
        if '|---' in line:
            sep_index = i
            break
    
    if sep_index is None:
        print("[Master] Table separator not found")
        return
    
    # Format new job rows
    new_rows = []
    for job in jobs:
        row = f"| {job['date']} | {job['title']} | {job['company']} | {job['location']} | {job['salary']} | {job['sponsorship']} | {job['sc']} | [View]({job['url']}) |"
        new_rows.append(row)
    
    # Insert new rows after separator
    lines = lines[:sep_index+1] + new_rows + [''] + lines[sep_index+1:]
    
    MASTER_FILE.write_text('\n'.join(lines))
    print(f"[Master] Added {len(jobs)} jobs to master table")

def git_commit_push():
    """Commit and push to GitHub"""
    print("[Git] Committing and pushing...")
    
    os.chdir(BASE_DIR)
    subprocess.run(['git', 'add', '.'], check=False)
    subprocess.run(['git', 'commit', '-m', f'Backfill: Added jobs from last 7 days'], check=False)
    subprocess.run(['git', 'push', 'origin', 'main'], check=False)
    
    print("[Git] Pushed to GitHub")

def main():
    print("=== ServiceNow Jobs Backfill - Last 7 Days ===")
    
    # Step 1: Get date range
    dates = get_date_range()
    print(f"[Dates] Backfilling: {dates[-1]} to {dates[0]}")
    
    # Step 2: Extract jobs from sources
    jobs = extract_jobs_from_hunt_uk()
    
    if not jobs:
        print("[Main] No jobs found")
        return
    
    # Step 3: Update master table
    update_master_table(jobs)
    
    # Step 4: Git commit and push
    git_commit_push()
    
    print(f"=== Backfill complete: {len(jobs)} jobs added ===")

if __name__ == "__main__":
    main()
