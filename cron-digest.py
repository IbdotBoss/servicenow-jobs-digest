#!/usr/bin/env python3
"""
ServiceNow Jobs Daily Digest Cron Script
- Scrapes multiple job sites
- Deduplicates against all-jobs.md (master table)
- Appends new jobs to master table
- Creates daily digest file
- Pushes to GitHub
"""

import os
import re
import subprocess
from datetime import datetime
from pathlib import Path

# Configuration
BASE_DIR = Path.home() / "hermes-workspace" / "servicenow-jobs-digest"
DOCS_DIR = BASE_DIR / "docs"
MASTER_FILE = DOCS_DIR / "all-jobs.md"
INDEX_FILE = DOCS_DIR / "index.md"

def get_today():
    return datetime.now().strftime("%Y-%m-%d")

def load_existing_jobs():
    """Load all existing jobs from master table for dedup"""
    if not MASTER_FILE.exists():
        return set()
    
    existing = set()
    content = MASTER_FILE.read_text()
    
    # Parse markdown table rows
    # Format: | Date | Job Title | Company | Location | Salary | Sponsorship | SC | Link |
    pattern = r'\|\s*[\d-]+\s*\|\s*(.+?)\s*\|\s*(.+?)\s*\|\s*.+?\s*\|\s*.+?\s*\|\s*[✓✗]\s*\|\s*[✓✗]\s*\|\s*\[View\]'
    
    for line in content.split('\n'):
        if line.startswith('|') and '---' not in line:
            parts = [p.strip() for p in line.split('|')]
            if len(parts) >= 4:
                job_title = parts[1].strip()
                company = parts[2].strip()
                if job_title and company:
                    existing.add(f"{job_title}|{company}")
    
    print(f"[Dedup] Loaded {len(existing)} existing jobs from master table")
    return existing

def scrape_jobs():
    """
    Scrape all 9 job sites for ServiceNow jobs with sponsorship in UK.
    Returns list of dicts: {title, company, location, salary, sponsorship, sc, link}
    """
    print("[Scrape] Starting job scrape across 9 sites...")
    
    # This is where the actual scraping happens
    # For now, return placeholder - the actual scrape logic needs to be implemented
    # using web_search, browser tools, or dedicated scrapers
    
    jobs = []
    
    # TODO: Implement actual scraping for:
    # - LinkedIn (script: linkedin.py)
    # - Indeed (script: indeed.py)
    # - CWJobs (script: cwjobs.py)
    # - Technojobs (script: technojobs.py)
    # - Prospects (script: prospects.py)
    # - Gradcracker (script: gradcracker.py)
    # - Milkround (script: milkround.py)
    # - CareerJet (script: careerjet.py)
    # - Adzuna (script: adzuna.py)
    
    print(f"[Scrape] Found {len(jobs)} total jobs")
    return jobs

def filter_new_jobs(jobs, existing_keys):
    """Filter out jobs that already exist in master table"""
    new_jobs = []
    for job in jobs:
        key = f"{job['title']}|{job['company']}"
        if key not in existing_keys:
            new_jobs.append(job)
            existing_keys.add(key)
    
    print(f"[Filter] {len(new_jobs)} new jobs after dedup")
    return new_jobs

def format_job_row(job, date):
    """Format a job as a markdown table row"""
    sponsorship = '✓' if job.get('sponsorship') else '✗'
    sc = '✓' if job.get('sc') else '✗'
    link = f"[View]({job['link']})"
    salary = job.get('salary', '-')
    location = job.get('location', 'UK')
    
    return f"| {date} | {job['title']} | {job['company']} | {location} | {salary} | {sponsorship} | {sc} | {link} |"

def update_master_table(new_jobs, date):
    """Append new jobs to master table (sorted newest first)"""
    if not new_jobs:
        print("[Master] No new jobs to add")
        return
    
    # Read existing content
    if MASTER_FILE.exists():
        content = MASTER_FILE.read_text()
    else:
        content = """---
layout: default
title: All Jobs - Master Archive
---

# Master Job Archive

All ServiceNow jobs ever found, sorted by date (newest → oldest).

**Legend:**
- **SC** = Security Clearance needed
- **Sponsorship** = ✓ Confirmed / ✗ Not mentioned

---

| Date | Job Title | Company | Location | Salary | Sponsorship | SC | Link |
|------|-----------|---------|----------|--------|-------------|----|------|
"""
    
    # Find the table end (after the separator row)
    lines = content.split('\n')
    table_start = 0
    for i, line in enumerate(lines):
        if line.startswith('|') and '---' in line:
            table_start = i + 1
            break
    
    # Insert new rows after the separator
    new_rows = [format_job_row(job, date) for job in new_jobs]
    lines = lines[:table_start] + new_rows + [''] + lines[table_start:]
    
    MASTER_FILE.write_text('\n'.join(lines))
    print(f"[Master] Added {len(new_jobs)} jobs to master table")

def create_daily_digest(new_jobs, date):
    """Create daily digest file"""
    digest_file = DOCS_DIR / f"{date}.md"
    
    content = f"""---
layout: default
title: ServiceNow Jobs Digest - {date}
date: {date}
---

# ServiceNow Jobs Digest - {date}

**{len(new_jobs)} new jobs found**

---

| Job Title | Company | Location | Salary | Sponsorship | SC | Link |
|-----------|---------|----------|--------|-------------|----|------|
"""
    
    for job in new_jobs:
        sponsorship = '✓' if job.get('sponsorship') else '✗'
        sc = '✓' if job.get('sc') else '✗'
        link = f"[View]({job['link']})"
        salary = job.get('salary', '-')
        location = job.get('location', 'UK')
        
        content += f"| {job['title']} | {job['company']} | {location} | {salary} | {sponsorship} | {sc} | {link} |\n"
    
    content += f"\n---\n\n*Digest generated on {date} at 08:00 UK time*\n"
    
    digest_file.write_text(content)
    print(f"[Digest] Created {digest_file}")
    return digest_file

def update_index(date):
    """Update index.md with link to new digest"""
    if not INDEX_FILE.exists():
        print("[Index] Index file not found, skipping")
        return
    
    content = INDEX_FILE.read_text()
    
    # Add link to new digest after "Latest Digest" section
    new_link = f"- [{date}]({date}.html)"
    
    if new_link not in content:
        # Insert after "Latest Digest" section
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if 'Latest Digest' in line:
                # Find next non-empty line and insert after it
                for j in range(i+1, len(lines)):
                    if lines[j].strip():
                        lines.insert(j, new_link)
                        break
                break
        
        INDEX_FILE.write_text('\n'.join(lines))
        print(f"[Index] Added link to {date} digest")

def git_commit_push(date, new_job_count):
    """Commit and push changes to GitHub"""
    os.chdir(BASE_DIR)
    
    subprocess.run(['git', 'add', '.'], check=False)
    subprocess.run(['git', 'commit', '-m', f"Daily digest {date} - {new_job_count} new jobs"], check=False)
    subprocess.run(['git', 'push', 'origin', 'main'], check=False)
    
    print(f"[Git] Pushed changes to GitHub")

def main():
    print(f"=== ServiceNow Jobs Digest - {get_today()} ===")
    
    # Step 1: Load existing jobs for dedup
    existing_keys = load_existing_jobs()
    
    # Step 2: Scrape jobs
    jobs = scrape_jobs()
    
    if not jobs:
        print("[Main] No jobs found, exiting")
        return
    
    # Step 3: Filter new jobs
    new_jobs = filter_new_jobs(jobs, existing_keys)
    
    if not new_jobs:
        print("[Main] No new jobs, exiting")
        return
    
    date = get_today()
    
    # Step 4: Update master table
    update_master_table(new_jobs, date)
    
    # Step 5: Create daily digest
    create_daily_digest(new_jobs, date)
    
    # Step 6: Update index
    update_index(date)
    
    # Step 7: Git commit and push
    git_commit_push(date, len(new_jobs))
    
    print(f"=== Done: {len(new_jobs)} new jobs added ===")

if __name__ == "__main__":
    main()
