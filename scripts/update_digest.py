#!/usr/bin/env python3
"""Update ServiceNow Jobs Digest for today"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import json
import re
from datetime import datetime
from pathlib import Path
from scripts.job_model import Job

# Configuration
BASE_DIR = Path.home() / "hermes-workspace" / "servicenow-jobs-digest"
DOCS_DIR = BASE_DIR / "docs"
MASTER_FILE = DOCS_DIR / "all-jobs.html"
INDEX = DOCS_DIR / "index.html"
TODAY = datetime.now().strftime("%Y-%m-%d")
DIGEST_FILE = DOCS_DIR / f"{TODAY}.html"

# Load jobs from JSON
JSON_FILE = DOCS_DIR / "data" / "jobs.json"
if JSON_FILE.exists():
    with open(JSON_FILE, 'r') as f:
        all_jobs = json.load(f)
    # Filter jobs for today
    today_jobs = [job for job in all_jobs if job.get('date') == TODAY]
else:
    today_jobs = []

def load_existing_jobs():
    """Load existing job URLs from all-jobs.html for dedup"""
    if not MASTER_FILE.exists():
        return set()
    
    content = MASTER_FILE.read_text()
    # Find all huntukvisasponsors.com/job/... URLs
    urls = set(re.findall(r'href=\"(https://huntukvisasponsors\.com/job/[^\"]+)\"', content))
    print(f"[Dedup] Loaded {len(urls)} existing job URLs")
    return urls

def generate_job_row(job):
    """Generate HTML table row for a job"""
    return f"""                <tr>
                    <td class=\"date\">{job['date']}</td>
                    <td><a href=\"{job['link']}\">{job['title']}</a></td>
                    <td class=\"company\">{job['company']}</td>
                    <td>{job['location']}</td>
                    <td class=\"symbol\">✓</td>
                    <td class=\"symbol\">✗</td>
                </tr>"""

def update_master_table(new_jobs):
    """Update all-jobs.html with new jobs"""
    existing_urls = load_existing_jobs()
    
    # Filter new jobs
    truly_new = [j for j in new_jobs if j['link'] not in existing_urls]
    print(f"[All-Jobs] {len(truly_new)} new jobs to add (out of {len(new_jobs)} scraped)")
    
    if not truly_new:
        print("[All-Jobs] No new jobs to add")
        return False
    
    # Read existing file
    if MASTER_FILE.exists():
        content = MASTER_FILE.read_text()
    else:
        # Create initial HTML structure
        content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>ServiceNow Jobs UK — Master Archive</title>
    <link rel=\"stylesheet\" href=\"https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap\">
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
        .subtitle { color: rgba(0,0,0.5); font-size: 0.9rem; margin-bottom: 40px; }
        
        table { width: 100%; border-collapse = collapse; margin: 24px 0; font-size: 0.9rem; }
        
        th {
            text-align = left;
            padding = 12px 16px;
            border-bottom = 2px solid #e5e5e5;
            font-weight = 700;
            font-size = 0.8rem;
            text-transform = uppercase;
            letter-spacing = 0.1em;
            color = rgba(0,0,0.4);
        }
        
        td {
            padding = 12px 12px 12px 0;
            border-bottom = 1px solid rgba(0,0,0.06);
            vertical-align = top;
        }
        
        td a {
            color = #0a0a0a;
            text-decoration = none;
            font-weight = 500;
        }
        
        td a:hover { text-decoration = underline; }
        
        .date { color = rgba(0,0,0.4); font-size = 0.85rem; white-space = nowrap; }
        .company { color = rgba(0,0,0.6); font-size = 0.85rem; }
        .symbol { font-size = 0.9rem; }
        
        .legend {
            margin = 16px 0 24px;
            font-size = 0.85rem;
            color = rgba(0,0,0.5);
            line-height = 1.8;
        }
        
        .note {
            margin-top = 24px;
            padding = 16px;
            background = rgba(0,0,0.02);
            border-left = 3px solid rgba(0,0,0.1);
            font-size = 0.85rem;
            color = rgba(0,0,0.5);
            line-height = 1.6;
        }
        
        footer {
            margin-top = 80px;
            padding-top = 24px;
            border-top = 1px solid rgba(0,0,0.06);
            font-size = 0.85rem;
            color = rgba(0,0,0.4);
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
            </tbody>
        </table>
        
        <div class=\"note\">
            <strong>Why direct URLs?</strong><br>
            You want to CLICK and APPLY immediately — not hunt through career pages.<br>
            Yes, these links expire in days. That's fine — the daily cron (05:00 UK) fetches FRESH ones.<br><br>
            <strong>I'm your scraper:</strong> Hunt UK is paywalled for you, but I can see and extract these links daily.
        </div>
        
        <footer>
            <p>Last updated: {datetime.now().strftime('%Y-%m-%d')} · {len(jobs)} direct job links</p>
            <p><a href=\"https://github.com/IbdotBoss/servicenow-jobs-digest\">View on GitHub</a></p>
        </footer>
    </div>
</body>
</html>"""
        with open(MASTER_FILE, 'w') as f:
            f.write(content)
        print(f"[Master] Created new master file: {MASTER_FILE}")

    # Read existing file
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
        return False
    
    # Format new job rows
    new_rows = []
    for job in new_jobs:
        row = f"""                <tr>
                    <td class=\"date\">{job['date']}</td>
                    <td><a href=\"{job['link']}\">{job['title']}</a></td>
                    <td class=\"company\">{job['company']}</td>
                    <td>{job['location']}</td>
                    <td class=\"symbol\">✓</td>
                    <td class=\"symbol\">✗</td>
                </tr>"""
        new_rows.append(row)
    
    # Insert new rows after separator
    lines = lines[:sep_index+1] + new_rows + [''] + lines[sep_index+1:]
    
    MASTER_FILE.write_text('\n'.join(lines))
    print(f"[Master] Added {len(new_jobs)} jobs to master table")
    return True

def update_index_html(jobs):
    """Update index.html with recent jobs (latest 6)"""
    job_rows = '\n'.join([generate_job_row(job) for job in jobs[:6]])
    
    content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>ServiceNow Jobs UK</title>
    <link rel=\"stylesheet\" href=\"https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap\">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #0a0a0a;
            background: #ffffff;
            line-height: 1.6;
            font-size: 16px;
        }}
        
        .container {{
            max-width: 680px;
            margin: 0 auto;
            padding: 60px 20px 100px;
        }}
        
        h1 {{
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 8px;
        }}
        
        .subtitle {{
            color: rgba(0,0,0.5);
            font-size: 0.9rem;
            margin-bottom: 60px;
        }}
        
        h2 {{
            font-size: 1.1rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            margin: 48px 0 16px;
        }}
        
        .job-count {{
            color: rgba(0,0,0.4);
            font-size: 0.85rem;
            margin-bottom: 24px;
        }}
        
        table {{
            width: 100%;
            border-collapse = collapse;
            margin = 24px 0;
            font-size = 0.9rem;
        }}
        
        th {{
            text-align = left;
            padding = 12px 16px;
            border-bottom = 2px solid #e5e5.5;
            font-weight = 700;
            font-size = 0.8rem;
            text-transform = uppercase;
            letter-spacing = 0.1em;
            color = rgba(0,0,0.4);
        }}
        
        td {{
            padding = 16px;
            border-bottom = 1px solid rgba(0,0,0.06);
        }}
        
        td:first-child {{
            color = rgba(0,0,0.4);
            font-size = 0.85rem;
            white-space = nowrap;
        }}
        
        a {{
            color = #0a0a0a;
            text-decoration = none;
            font-weight = 500;
        }}
        
        a:hover {{
            text-decoration = underline;
        }}
        
        .view-all {{
            display: inline-block;
            margin-top = 32px;
            padding = 12px 24px;
            border = 1px solid #e5.5;
            border-radius = 8px;
            color = #0a0a0a;
            text-decoration = none;
            font-size = 0.9rem;
            font-weight = 500;
            transition = all 0.2s;
        }}
        
        .view-all:hover {{
            background = #fafafa;
        }}
        
        .legend {{
            margin-top = 48px;
            padding = 24px;
            background = #fafafa;
            border-radius = 8px;
            font-size = 0.85rem;
            color = rgba(0,0,0.6);
        }}
        
        .legend strong {{
            font-weight = 700;
            color = #0a0a0a;
        }}
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>ServiceNow Jobs UK</h1>
        <p class=\"subtitle\">Verified visa sponsorship jobs, updated daily.</p>
        
        <h2>Latest Jobs</h2>
        <p class=\"job-count\">{len(jobs)} jobs found today</p>
        
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Job Title</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>✓</th>
                </tr>
            </thead>
            <tbody>
{job_rows}
            </tbody>
        </table>
        
        <a href=\"all-jobs.html\" class=\"view-all\">View All Jobs →</a>
        
        <div class=\"legend\">
            <p><strong>Legend:</strong></p>
            <p>✓ = Sponsorship available (verified by Hunt UK)</p>
            <p>SC = Security Clearance needed</p>
            <p><strong>Note:</strong> Job links expire after a few days — that's fine, the job poster just removed it.</p>
        </div>
    </div>
</body>
</html>"""
    
    INDEX.write_text(content)
    print(f"[Index] Updated with {len(jobs)} latest jobs")

def create_digest_file(jobs):
    """Create today's digest file"""
    if DIGEST_FILE.exists():
        print(f"[Digest] {TODAY}.html already exists, skipping")
        return
    
    job_rows = '\n'.join([generate_job_row(job) for job in jobs])
    
    content = f"""<!DOCTYPE html>
<html lang=\"en\">
<head>
    <meta charset=\"UTF-8\">
    <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\">
    <title>ServiceNow Jobs Digest — {TODAY}</title>
    <link rel=\"stylesheet\" href=\"https://api.fontshare.com/v2/css?f[]=satoshi@400,500,700&display=swap\">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        
        body {{
            font-family: 'Satoshi', -apple-system, BlinkMacSystemFont, sans-serif;
            color: #0a0a0a;
            background: #ffffff;
            line-height: 1.6;
            font-size: 16px;
        }}
        
        .container {{
            max-width: 680px;
            margin: 0 auto;
            padding: 60px 20px 100px;
        }}
        
        h1 {{
            font-size: 2rem;
            font-weight: 700;
            letter-spacing: -0.03em;
            margin-bottom: 8px;
        }}
        
        .subtitle {{
            color: rgba(0,0,0.5);
            font-size: 0.9rem;
            margin-bottom: 60px;
        }}
        
        table {{
            width: 100%;
            border-collapse = collapse;
            margin = 24px 0;
            font-size = 0.9rem;
        }}
        
        th {{
            text-align = left;
            padding = 12px 16px;
            border-bottom = 2px solid #e5.5;
            font-weight = 700;
            font-size = 0.8rem;
            text-transform = uppercase;
            letter-spacing = 0.1em;
            color = rgba(0,0,0.4);
        }}
        
        td {{
            padding = 16px;
            border-bottom = 1px solid #f5.5;
        }}
        
        a {{
            color = #0a0a0a;
            text-decoration = none;
            font-weight = 500;
        }}
        
        a:hover {{
            text-decoration = underline;
        }}
    </style>
</head>
<body>
    <div class=\"container\">
        <h1>Digest — {TODAY}</h1>
        <p class=\"subtitle\">{len(jobs)} new ServiceNow jobs found today</p>
        
        <table>
            <thead>
                <tr>
                    <th>Date</th>
                    <th>Job Title</th>
                    <th>Company</th>
                    <th>Location</th>
                    <th>✓</th>
                </tr>
            </thead>
            <tbody>
{job_rows}
            </tbody>
        </table>
        
        <p style=\"margin-top: 48px; font-size: 0.85rem; color: rgba(0,0,0.4);\">
            Digest generated on {TODAY} at 12:00 UK time
        </p>
    </div>
</body>
</html>"""
    
    DIGEST_FILE.write_text(content)
    print(f"[Digest] Created {TODAY}.html")

if __name__ == "__main__":
    print(f"=== ServiceNow Jobs Digest — {TODAY} ===")
    
    # Load jobs from JSON
    if not JSON_FILE.exists():
        print(f"[JSON] File not found: {JSON_FILE}")
        exit(1)
    
    with open(JSON_FILE, 'r') as f:
        all_jobs = json.load(f)
    
    # Filter today's jobs
    today_jobs = [job for job in all_jobs if job.get('date') == TODAY]
    
    if not today_jobs:
        print("[Main] No jobs found for today")
        exit(1)
    
    # Step 1: Update master table
    update_master_table(today_jobs)
    
    # Step 2: Update index HTML
    update_index_html(today_jobs)
    
    # Step 3: Create today's digest file
    create_digest_file(today_jobs)
    
    print(f"\n=== Done: {len(today_jobs)} jobs processed ===")