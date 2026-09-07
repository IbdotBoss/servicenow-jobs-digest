#!/usr/bin/env python3
"""Test Bright Data superproxy with different auth formats."""
import json, urllib.request, urllib.error, re, base64

key = open('.env').read().strip().split('=',1)[1].strip()

# Try different proxy auth formats
# Format 1: brd-customer-{ID}:pass@host (ID = first part of API key, pass = empty or key)
# Format 2: Using the /request API with zone that matches the customer ID

# Actually, let's try the simplest thing: just use Bright Data's free 5K credits
# to scrape a LinkedIn jobs search page directly via /request with zone=unlocker
# But we know that fails.

# Alternative: use DuckDuckGo's lite version which may be more accessible
search_url = 'https://lite.duckduckgo.com/lite/?q=servicenow+linkedin+jobs+UK'
req = urllib.request.Request(search_url, headers={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
})
try:
    with urllib.request.urlopen(req, timeout=15) as r:
        html = r.read().decode('utf-8', 'ignore')
        urls = re.findall(r'https://www\.linkedin\.com/jobs/view/(\d+)', html)
        print(f"DDG Lite: found {len(set(urls))} LinkedIn job URLs")
        for u in sorted(set(urls))[:5]:
            print(f"  https://www.linkedin.com/jobs/view/{u}")
        if not urls:
            # Check what links exist
            all_links = re.findall(r'href="(https?://[^"]+)"', html)
            print(f"  Total links: {len(all_links)}")
            for l in all_links[:5]:
                print(f"  {l[:100]}")
except Exception as e:
    print(f"DDG Lite failed: {e}")

# Also try Bing
print("\n--- Trying Bing ---")
bing_url = 'https://www.bing.com/search?q=servicenow+site:linkedin.com/jobs/view+UK'
req2 = urllib.request.Request(bing_url, headers={
    'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
})
try:
    with urllib.request.urlopen(req2, timeout=15) as r:
        html2 = r.read().decode('utf-8', 'ignore')
        urls2 = re.findall(r'https://www\.linkedin\.com/jobs/view/(\d+)', html2)
        print(f"Bing: found {len(set(urls2))} LinkedIn job URLs")
        for u in sorted(set(urls2))[:5]:
            print(f"  https://www.linkedin.com/jobs/view/{u}")
except Exception as e:
    print(f"Bing failed: {e}")
