#!/usr/bin/env python3
"""
ServiceNow Jobs Daily Digest - Cron Script
- Runs all scrapers
- Saves JSON data
- Generates static HTML files
- Pushes to GitHub
"""

import os
import subprocess
from datetime import datetime
from pathlib import Path
from multi_scrape import scrape_all_sources
from generate_archive import generate_archive

# Configuration
BASE_DIR = Path.home() / "hermes-workspace" / "servicenow-jobs-digest"
DOCS_DIR = BASE_DIR / "docs"
DATA_DIR = DOCS_DIR / "data"
JSON_FILE = DATA_DIR / "jobs.json"

# Ensure directories exist
DATA_DIR.mkdir(parents=True, exist_ok=True)

def main():
    print("="*60)
    print("DAILY SERVICE NOW JOBS DIGEST - CRON JOB")
    print("="*60)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Step 1: Run all scrapers
    print("Step 1/3: Running multi-source scrape...")
    jobs = scrape_all_sources()
    print(f"Total unique jobs scraped: {len(jobs)}")
    
    if not jobs:
        print("Error: No jobs found! Exiting.")
        return
    
    # Step 2: Save JSON data
    print("Step 2/3: Saving JSON data...")
    import json
    with open(JSON_FILE, 'w') as f:
        json.dump([j.to_dict() for j in jobs], f, indent=2)
    
    # Step 3: Generate static HTML files
    print("Step 3/3: Generating static HTML files...")
    generate_archive()
    
    # Step 4: Update GitHub Pages
    print("Step 4/3: Updating GitHub repository...")
    try:
        # Add changes
        subprocess.run(['git', 'add', '.'], cwd=BASE_DIR, check=True, capture_output=True)
        
        # Commit
        commit_msg = f"Daily digest update - {datetime.now().strftime('%Y-%m-%d')} - {len(jobs)} jobs"
        subprocess.run(['git', 'commit', '-m', commit_msg], cwd=BASE_DIR, check=True, capture_output=True)
        
        # Push
        subprocess.run(['git', 'push', 'origin', 'main'], cwd=BASE_DIR, check=True, capture_output=True)
        
        print("✅ Successfully pushed to GitHub")
    except subprocess.CalledProcessError as e:
        print(f"❌ Git error: {e}")
        print(f"Output: {e.stdout.decode()}")
        print(f"Error: {e.stderr.decode()}")
    
    print()
    print("="*60)
    print("CRON JOB COMPLETED SUCCESSFULLY")
    print(f"Total jobs in archive: {len(jobs)}")
    print("="*60)

if __name__ == "__main__":
    main()