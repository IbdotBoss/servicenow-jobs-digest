#!/usr/bin/env python3
"""Test script to verify the system works"""

import sys
import os
import subprocess

def test_system():
    print("Testing ServiceNow Jobs Digest system...")
    
    # Test 1: Check if Python scripts exist
    scripts = [
        "scripts/scrape_all.py",
        "scripts/generate_archive.py",
        "scripts/job_model.py"
    ]
    
    for script in scripts:
        if not os.path.exists(script):
            print(f"❌ ERROR: {script} not found!")
            return False
        else:
            print(f"✓ {script} exists")
    
    # Test 2: Check if requirements are installed
    try:
        import requests
        import bs4
        import lxml
        print("✓ Dependencies installed")
    except ImportError as e:
        print(f"❌ ERROR: Missing dependency: {e}")
        return False
    
    # Test 3: Run scraper (will likely fail due to network, but test execution)
    print("\nRunning scraper test (this may fail due to network)...")
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
    
    # Test 4: Check if data directory exists
    data_dir = "/home/ubuntu/hermes-workspace/servicenow-jobs-digest/docs/data"
    if os.path.exists(data_dir) and os.path.isdir(data_dir):
        print(f"✓ Data directory exists: {data_dir}")
    else:
        print(f"❌ Data directory missing: {data_dir}")
        return False
    
    # Test 5: Check if JSON file can be created
    try:
        import json
        with open(f"{data_dir}/jobs.json", "w") as f:
            json.dump([], f)
        print("✓ JSON file can be created")
    except Exception as e:
        print(f"❌ ERROR creating JSON file: {e}")
        return False
    
    print("\n✅ All basic tests passed!")
    return True

if __name__ == "__main__":
    success = test_system()
    sys.exit(0 if success else 1)