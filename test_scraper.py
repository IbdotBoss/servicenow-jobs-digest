#!/usr/bin/env python3
"""Test script to load and run a scraper via importlib"""

import sys
import importlib.util

# Load the cwjobs_scraper module
scraper_file = "/home/ubuntu/hermes-workspace/servicenow-jobs-digest/scripts/scrapers/cwjobs_scraper.py"
spec = importlib.util.spec_from_file_location("cwjobs_scraper", scraper_file)
module = importlib.util.module_from_spec(spec)

try:
    spec.loader.exec_module(module)
    print("Successfully imported cwjobs_scraper module")
    
    # Find the CWJobsScraper class
    if hasattr(module, 'CWJobsScraper'):
        scraper_class = module.CWJobsScraper
        scraper = scraper_class()
        print("Scraper initialized")
        
        # Run the scraper
        import asyncio
        jobs = asyncio.run(scraper.run())
        print(f"Found {len(jobs)} jobs from CWJobs")
        
        # Check if jobs were saved to database
        import sqlite3
        conn = sqlite3.connect('jobs.db')
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM jobs")
        count = cursor.fetchone()[0]
        print(f"Total jobs in database: {count}")
        conn.close()
    else:
        print("CWJobsScraper class not found")
        
except Exception as e:
    print(f"Error: {e}")
    import traceback
    traceback.print_exc()