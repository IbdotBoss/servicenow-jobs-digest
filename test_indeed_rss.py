#!/usr/bin/env python3
"""
Test Indeed RSS feed
"""

import requests
from bs4 import BeautifulSoup

url = "https://www.indeed.com/jobs?q=ServiceNow&r=uk&format=rss"

try:
    response = requests.get(url, timeout=30)
    print(f"Status code: {response.status_code}")
    if response.status_code == 200:
        soup = BeautifulSoup(response.text, 'xml')
        items = soup.find_all('item')
        print(f"Found {len(items)} items in RSS feed")
        for item in items[:3]:
            title = item.title.text if item.title else 'N/A'
            link = item.link.text if item.link else 'N/A'
            print(f"  - {title}")
            print(f"    Link: {link}")
except Exception as e:
    print(f"Error: {e}")