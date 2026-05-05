#!/usr/bin/env python3
"""Test each scraper individually"""

import subprocess
import sys
import os

# Add scripts directory to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scripts'))

scrapers = [
    ("Hunt UK", "python scripts/scrapers/hunt_uk_playwright_scraper.py"),
    ("CWJobs", "python scripts/scrapers/cwjobs_scraper.py"),
    ("Technojobs", "python scripts/scrapers/technojobs_scraper.py"),
    ("Prospects", "python scripts/scrapers/prospects_scraper.py"),
    ("Gradcracker", "python scripts/scrapers/gradcracker_scraper.py"),
    ("Milkround", "python scripts/scrapers/milkround_scraper.py"),
    ("CareerJet", "python scripts/scrapers/careerjet_scraper.py"),
    ("Adzuna", "python scripts/scrapers/adzuna_scraper.py"),
]

print("Testing each scraper individually...\n")
for name, command in scrapers:
    print(f"Testing {name}... ", end="")
    sys.stdout.flush()
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=120
        )
        
        if result.returncode == 0:
            print("✓ PASSED")
        else:
            print(f"✗ FAILED (exit code {result.returncode})")
            if result.stderr:
                print(f"   Error: {result.stderr[:200]}")
    except subprocess.TimeoutExpired:
        print("✗ TIMEOUT")
    except Exception as e:
        print(f"✗ ERROR: {e}")

print("\nAll scraper tests completed!")
