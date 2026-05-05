#!/usr/bin/env python3
"""
Check for iframes on the page
"""

import requests
from bs4 import BeautifulSoup

response = requests.get("https://huntukvisasponsors.com/jobs", timeout=30)
soup = BeautifulSoup(response.text, 'html.parser')

iframes = soup.find_all('iframe')
print(f"Found {len(iframes)} iframes")
for i, iframe in enumerate(iframes[:5]):
    src = iframe.get('src', '')
    print(f"Iframe {i+1}: src={src}")