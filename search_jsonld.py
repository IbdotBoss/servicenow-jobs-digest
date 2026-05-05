#!/usr/bin/env python3
"""
Search for JSON-LD patterns in page source
"""

import requests
import re
from bs4 import BeautifulSoup

# Get page source
response = requests.get("https://huntukvisasponsors.com/jobs", timeout=30)
content = response.text

# Search for JSON-LD patterns
print("Searching for JSON-LD patterns...")
print(f"Page length: {len(content)} characters")

# Look for @context or @type
if '"@context"' in content:
    print('Found "@context" in content')
else:
    print('No "@context" found')

if '"@type"' in content:
    print('Found "@type" in content')
else:
    print('No "@type" found')

# Look for schema.org
if 'schema.org' in content:
    print('Found "schema.org" in content')
else:
    print('No "schema.org" found')

# Look for ItemList
if 'ItemList' in content:
    print('Found "ItemList" in content')
else:
    print('No "ItemList" found')

# Look for JobPosting
if 'JobPosting' in content:
    print('Found "JobPosting" in content')
else:
    print('No "JobPosting" found')

# Search for script tags with JSON
script_tags = re.findall(r'<script[^>]*type="application/ld\+json"[^>]*>(.*?)</script>', content, re.DOTALL)
if script_tags:
    print(f'Found {len(script_tags)} script tags with type "application/ld+json"')
    for i, script in enumerate(script_tags[:3]):
        print(f"  Script {i+1}: {script[:100]}...")
else:
    print('No script tags with type "application/ld+json" found')

# Search for any script tags containing JSON
all_scripts = re.findall(r'<script[^>]*>(.*?)</script>', content, re.DOTALL)
print(f"\nFound {len(all_scripts)} script tags in total")
for script in all_scripts[:5]:
    if '{' in script and '}' in script:
        print(f"  Script with JSON content: {script[:100]}...")