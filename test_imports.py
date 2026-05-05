#!/usr/bin/env python3
"""Test script to verify all scrapers can be initialized"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import asyncio

# List of scraper modules to test
scraper_modules = [
    'scripts.scrapers.hunt_uk_playwright_scraper',
    'scripts.scrapers.cwjobs_scraper',
    'scripts.scrapers.technojobs_scraper',
    'scripts.scrapers.prospects_scraper',
    'scripts.scrapers.gradcracker_scraper',
    'scripts.scrapers.milkround_scraper',
    'scripts.scrapers.careerjet_scraper',
    'scripts.scrapers.adzuna_scraper',
]

print("Testing scraper module imports...")
for module_name in scraper_modules:
    try:
        __import__(module_name)
        print(f"✓ Successfully imported {module_name}")
    except Exception as e:
        print(f"✗ Failed to import {module_name}: {e}")

print("\nAll import tests completed!")
