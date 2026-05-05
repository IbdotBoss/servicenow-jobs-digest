#!/usr/bin/env python3
"""
Test the Hunt UK API endpoint directly
"""

import requests
import json

url = "https://api.huntukvisasponsors.com/api/v1/search/jobs/facets"

params = {
    "search": "ServiceNow",
    "location": "United Kingdom",
    "limit": 50,
}

headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'application/json',
    'Referer': 'https://huntukvisasponsors.com/jobs',
}

try:
    response = requests.get(url, params=params, headers=headers, timeout=30)
    print(f"Status: {response.status_code}")
    print(f"Content-Type: {response.headers.get('content-type', '')}")
    
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"JSON data received!")
            print(f"Keys: {list(data.keys())}")
            if 'jobs' in data:
                print(f"Found {len(data['jobs'])} jobs")
                for job in data['jobs'][:3]:
                    print(f"  - {job.get('title', 'N/A')} at {job.get('company', 'N/A')}")
            else:
                print(f"JSON preview: {json.dumps(data, indent=2)[:300]}...")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response text: {response.text[:500]}...")
    else:
        print(f"Response: {response.text[:300]}...")
except Exception as e:
    print(f"Error: {e}")