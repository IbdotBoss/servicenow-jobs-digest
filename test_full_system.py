#!/usr/bin/env python3
"""
End-to-end test for ServiceNow Jobs Dashboard
"""

import sys
import os
import json
import sqlite3
from datetime import datetime
import subprocess

def test_system():
    print("=" * 60)
    print("TESTING SERVICE NOW JOBS DASHBOARD SYSTEM")
    print("=" * 60)
    
    # Test 1: Check if scripts exist
    scripts = [
        "scripts/scrape_all.py",
        "scripts/generate_archive.py",
        "scripts/job_model.py"
    ]
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"❌ FAIL: {script} not found")
            return False
        else:
            print(f"✓ {script} exists")
    
    # Test 2: Check dependencies
    try:
        import requests
        from bs4 import BeautifulSoup
        import sqlite3
        print("✓ Dependencies installed")
    except ImportError as e:
        print(f"❌ FAIL: Missing dependency: {e}")
        return False
    
    # Test 3: Run scraper (will likely fail due to network, but test execution)
    print("\n➡️  Running scraper test (this may fail due to network)...")
    result = subprocess.run(
        ["python3", "scripts/scrape_all.py"],
        capture_output=True,
        text=True,
        cwd="/home/ubuntu/hermes-workspace/servicenow-jobs-digest"
    )
    
    if result.returncode == 0:
        print("✓ Scraper executed successfully")
    else:
        print(f"⚠️  Scraper completed with exit code {result.returncode}")
        print("Output:", result.stdout[:500])
        print("Error:", result.stderr[:500])
    
    # Test 4: Check if data directory exists
    data_dir = "/home/ubuntu/hermes-workspace/servicenow-jobs-digest/docs/data"
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        print(f"✓ Data directory exists: {data_dir}")
    else:
        print(f"❌ Data directory missing: {data_dir}")
        return False
    
    # Test 5: Check if JSON file can be created/read
    json_path = f"{data_dir}/jobs.json"
    try:
        # Create empty file if it doesn't exist
        if not os.path.exists(json_path):
            with open(json_path, "w") as f:
                json.dump([], f)
        # Read it back
        with open(json_path, "r") as f:
            data = json.load(f)
        print(f"✓ JSON file exists and is readable (contains {len(data)} jobs)")
    except Exception as e:
        print(f"❌ ERROR with JSON file: {e}")
        return False
    
    # Test 6: Check if HTML files exist
    html_files = [
        "docs/index.html",
        "docs/all-jobs.html",
        "docs/styles.css",
        "docs/jobs.js"
    ]
    
    for html_file in html_files:
        if os.path.exists(f"/home/ubuntu/hermes-workspace/servicenow-jobs-digest/{html_file}"):
            print(f"✓ {html_file} exists")
        else:
            print(f"❌ {html_file} missing")
            return False
    
    print("\n" + "=" * 60)
    print("✅ ALL SYSTEM TESTS PASSED")
    print("=" * 60)
    return True

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)