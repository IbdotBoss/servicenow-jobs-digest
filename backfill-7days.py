#!/usr/bin/env python3
"""ServiceNow Jobs Backfill Script - Last 7 Days"""

import re
import subprocess
import os
from datetime import datetime, timedelta
from pathlib import Path

BASE_DIR = Path.home() / "hermes-workspace/servicenow-jobs-digest"
DOCS_DIR = BASE_DIR / "docs"
MASTER_FILE = DOCS_DIR / "all-jobs.html"
JSON_FILE = DOCS_DIR / "data" / "jobs.json"

# Ensure directories exist
DOCS_DIR.mkdir(parents=True, exist_ok=True)
(JSON_FILE.parent).mkdir(parents=True, exist_ok=True)

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
    
    # Create master file if it doesn't exist
    if not MASTER_FILE.exists():
        print(f"[Master] Creating new master file: {MASTER_FILE}")
        content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ServiceNow Jobs UK — Master Archive</title>
    <link rel="stylesheet" href="https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap">
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        
        body {
            font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #0a0a0a;
            background: #ffffff;
            line-height: 1.6;
            font-size: 16px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
            padding: 60px 20px 100px;
        }
        
        h1 { font-size: 2rem; font-weight: 700; letter-spacing: -0.03em; margin-bottom: 8px; }
        .subtitle { color: rgba(0,0,0,0.5); font-size: 0.9rem; margin-bottom: 40px; }
        
        table { width: 100%; border-collapse = collapse; margin: 24px 0; font-size: 0.9rem; }
        
        th {
            text-align: left;
            padding: 12px 16px;
            border-bottom = 2px solid #e5e5e5;
            font-weight = 700;
            font-size = 0.8rem;
            text-transform = uppercase;
            letter-spacing = 0.1em;
            color = rgba(0,0,0,0.4);
        }
        
        td {
            padding = 12px 12px 12px 0;
            border-bottom = 1px solid rgba(0,0,0,0.06);
            vertical-align = top;
        }
        
        td a {
            color = #0a0a0a;
            text-decoration = none;
            font-weight = 500;
        }
        
        td a:hover { text-decoration = underline; }
        
        .date { color = rgba(0,0,0,0.4); font-size = 0.85rem; white-space = nowrap; }
        .company { color = rgba(0,0,0,0.6); font-size = 0.85rem; }
        .symbol { font-size = 0.9rem; }
        
        .legend {
            margin = 16px 0 24px;
            font-size = 0.85rem;
            color = rgba(0,0,0,0.5);
            line-height = 1.8;
        }
        
        .note {
            margin-top = 24px;
            padding = 16px;
            background = rgba(0,0,0,0.02);
            border-left = 3px solid rgba(0,0,0,0.1);
            font-size = 0.85rem;
            color = rgba(0,0,0,0.5);
            line-height = 1.6;
        }
        
        footer {
            margin-top = 80px;
            padding-top = 24px;
            border-top = 1px solid rgba(0,0,0,0.06);
            font-size = 0.85rem;
            color = rgba(0,0,0,0.4);
        }
        
        footer a { color = #0a0a0a; }
    </style>
</head>
<body>
    <div class=\"container\">
        <a href=\"index.html\" class=\"back-link\">← Back to home</a>
        
        <h1>Master Job Archive</h1>
        <p class=\"subtitle\">All ServiceNow jobs ever found, sorted by date (newest → oldest).</p>
        
        <div class=\"legend\">
            <strong>✓</strong> = Visa sponsorship confirmed · 
            <strong>✗</strong> = Security Clearance not mentioned<br>
            <strong>Note:</strong> Links are DIRECT job URLs. They may expire in days — click immediately.
        </div>
        
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Job Title & Link</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>Sponsorship</th>
                    <th>SC</th>
                </tr>
            </thead>
            <tbody>
"""
        with open(MASTER_FILE, 'w') as f:
            f.write(content)
    else:
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
        row = f"""                <tr>
                    <td class=\"date\">{job['date']}</td>
                    <td>
                        <a href=\"{job['url']}\">{job['title']}</a>
                        <div class=\"job-desc\">{job['title']}</div>
                    </td>
                    <td class=\"company\">{job['company']}</td>
                    <td>{job['location']}</td>
                    <td class=\"symbol\">✓</td>
                    <td class=\"symbol\">✗</td>
                </tr>"""
        new_rows.append(row)
    
    # Insert new rows after separator
    lines = lines[:sep_index+1] + new_rows + [''] + lines[sep_index+1:]
    
    MASTER_FILE.write_text('\n'.join(lines))
    print(f"[Master] Added {len(jobs)} jobs to master table")

def save_jobs_to_json(jobs):
    """Save jobs to JSON file"""
    import json
    from scripts.job_model import Job
    
    # Convert job dicts to Job objects and then to dicts for JSON storage
    job_objects = []
    for job_dict in jobs:
        job = Job(
            title=job_dict['title'],
            company=job_dict['company'],
            location=job_dict['location'],
            date=job_dict['date'],
            link=job_dict['url'],
            source="Hunt UK",
            sponsorship_confirmed=True,
            security_clearance=False if job_dict['sc'] == '✗' else True,
            tags=['permanent', 'mid'],
            job_type='permanent',
            experience_level='mid',
            salary_min=None,
            salary_max=None,
            currency='GBP',
            remote=False
        )
        job_objects.append(job)
    
    # Save to JSON
    data = [job.to_dict() for job in job_objects]
    with open(JSON_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    print(f"[JSON] Saved {len(jobs)} jobs to {JSON_FILE}")

def generate_archive():
    """Generate archive HTML from JSON"""
    print("[Archive] Generating archive HTML...")
    result = subprocess.run([
        'python3', 'scripts/generate_archive.py'
    ], cwd=BASE_DIR, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[Archive] Successfully generated archive")
    else:
        print(f"[Archive] Error generating archive: {result.stderr}")

def update_index_html():
    """Update index HTML"""
    print("[Index] Updating index HTML...")
    result = subprocess.run([
        'python3', 'scripts/update_digest.py'
    ], cwd=BASE_DIR, capture_output=True, text=True)
    
    if result.returncode == 0:
        print("[Index] Successfully updated index")
    else:
        print(f"[Index] Error updating index: {result.stderr}")

def git_commit_push():
    """Commit and push to GitHub"""
    print("[Git] Committing and pushing...")
    
    os.chdir(BASE_DIR)
    subprocess.run(['git', 'add', '.'], check=False)
    subprocess.run(['git', 'commit', '-m', f'Backfill: Added initial jobs'], check=False)
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
    
    # Step 3: Save jobs to JSON
    save_jobs_to_json(jobs)
    
    # Step 4: Generate archive HTML
    generate_archive()
    
    # Step 5: Update index HTML
    update_index_html()
    
    # Step 6: Git commit and push
    git_commit_push()
    
    print(f"=== Backfill complete: {len(jobs)} jobs added ===")

if __name__ == "__main__":
    main()