#!/usr/bin/env python3
"""
Inspect HTML structure of job sites
"""

import requests
from bs4 import BeautifulSoup

sites = [
    ("Reed", "https://www.reed.co.uk/jobs"),
    ("Totaljobs", "https://www.totaljobs.com"),
]

for name, url in sites:
    print(f"\n=== {name} ({url}) ===")
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find all div elements
            div_count = 0
            for div in soup.find_all('div'):
                classes = div.get('class', [])
                if classes:
                    div_count += 1
                    if div_count <= 20:
                        print(f"Div {div_count}: classes={classes}")
                    
            # Look for job-related keywords
            text = soup.get_text().lower()
            keywords = ['job', 'vacancy', 'career', 'apply']
            for keyword in keywords:
                count = text.count(keyword)
                print(f"  '{keyword}' appears {count} times")
                
        else:
            print(f"  Failed: status {response.status_code}")
    except Exception as e:
        print(f"  Error: {e}")