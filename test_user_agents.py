#!/usr/bin/env python3
"""
Test different user-agents for Hunt UK
"""

import requests

user_agents = [
    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (Windows NT 6.1; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
]

test_urls = [
    "https://huntukvisasponsors.com/jobs",
    "https://huntukvisasponsors.com/api/jobs",
    "https://huntukvisasponsors.com/graphql",
]

for url in test_urls:
    print(f"\nTesting: {url}")
    for ua in user_agents:
        try:
            response = requests.get(url, headers={'User-Agent': ua}, timeout=10)
            if response.status_code == 200:
                print(f"  User-Agent: {ua[:50]}...")
                print(f"  Status: {response.status_code}")
                print(f"  Content-Type: {response.headers.get('content-type', '')}")
                if len(response.text) < 1000:
                    print(f"  Content preview: {response.text[:500]}...")
                else:
                    print(f"  Content length: {len(response.text)}")
                break
        except:
            continue
    else:
        print(f"  All user-agents failed for {url}")

print("\nDone.")