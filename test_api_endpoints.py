#!/usr/bin/env python3
"""
Test direct API endpoints for Hunt UK
"""

import requests
import json

test_urls = [
    "https://huntukvisasponsors.com/api/jobs",
    "https://huntukvisasponsors.com/graphql",
    "https://huntukvisasponsors.com/.netlify/functions/jobs",
    "https://huntukvisasponsors.com/api/v1/jobs",
    "https://huntukvisasponsors.com/data/jobs.json",
]

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
}

for url in test_urls:
    try:
        print(f"Testing: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"  Status: {response.status_code}")
        if response.status_code == 200:
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                try:
                    data = response.json()
                    print(f"  JSON data found!")
                    print(f"  Preview: {json.dumps(data, indent=2)[:200]}...")
                except:
                    print(f"  Response appears to be JSON but could not parse")
            else:
                print(f"  Content-Type: {content_type}")
        else:
            print(f"  Response: {response.text[:100]}...")
        print()
    except Exception as e:
        print(f"  Error: {e}\n")