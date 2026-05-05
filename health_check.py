#!/usr/bin/env python3
"""
Health check for ServiceNow Jobs Dashboard
"""

import os
import sys
import subprocess
import json
import sqlite3
from datetime import datetime

def check_system():
    print("=" * 60)
    print("SERVICE NOW JOBS DASHBOARD - HEALTH CHECK")
    print("=" * 60)
    
    # Check 1: Python scripts
    scripts = [
        "scripts/scrape_all.py",
        "scripts/generate_archive.py",
        "scripts/job_model.py"
    ]
    for script in scripts:
        if os.path.exists(script):
            print(f"✓ {script} exists")
        else:
            print(f"❌ {script} missing")
            return False
    
    # Check 2: Dependencies
    try:
        import requests
        from bs4 import BeautifulSoup
        import sqlite3
        print("✓ Dependencies installed")
    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        return False
    
    # Check 3: Database
    try:
        conn = sqlite3.connect("jobs.db")
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs")
        count = cursor.fetchone()[0]
        print(f"✓ Database OK - {count} jobs")
        conn.close()
    except Exception as e:
        print(f"❌ Database error: {e}")
        return False
    
    # Check 4: Data directory
    data_dir = "docs/data"
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        print(f"✓ Data directory exists: {data_dir}")
    else:
        print(f"❌ Data directory missing: {data_dir}")
        return False
    
    # Check 5: JSON file
    json_path = f"{data_dir}/jobs.json"
    if os.path.exists(json_path):
        try:
            with open(json_path, "r") as f:
                data = json.load(f)
            print(f"✓ JSON file exists with {len(data)} jobs")
        except Exception as e:
            print(f"❌ JSON file error: {e}")
            return False
    else:
        print("⚠️  JSON file not found (may be empty)")
    
    # Check 6: HTML files
    html_files = ["docs/index.html", "docs/all-jobs.html", "docs/styles.css", "docs/jobs.js"]
    for html_file in html_files:
        if os.path.exists(html_file):
            print(f"✓ {html_file} exists")
        else:
            print(f"❌ {html_file} missing")
            return False
    
    print("=" * 60)
    print("✅ HEALTH CHECK PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = check_system()
    sys.exit(0 if success else 1)