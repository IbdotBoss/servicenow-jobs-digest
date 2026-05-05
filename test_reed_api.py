#!/usr/bin/env python3
"""
Test Reed API
"""

import requests
import json

url = "https://www.reed.co.uk/api2/jobs?keywords=ServiceNow&location=United Kingdom"

try:
    response = requests.get(url, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        try:
            data = response.json()
            print(f"Found {len(data)} jobs")
            for job in data[:3]:
                print(f"  - {job.get('jobTitle')} at {job.get('employerName', 'N/A')}")
        except Exception as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response: {response.text[:500]}...")
    else:
        print(f"Error: {response.text[:500]}")
except Exception as e:
    print(f"Error: {e}")