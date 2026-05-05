#!/usr/bin/env python3
"""
Debug script to test API endpoint directly with longer delay
"""

import asyncio
from playwright.async_api import async_playwright
import json

async def main():
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(
        headless=True,
        args=['--no-sandbox', '--disable-dev-shm-usage']
    )
    context = await browser.new_context(
        viewport={'width': 1920, 'height': 1080}
    )
    page = await context.new_page()
    
    # Set headers
    await context.set_extra_http_headers({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'application/json',
        'Referer': 'https://huntukvisasponsors.com/jobs',
    })
    
    # Navigate to jobs page first
    await page.goto("https://huntukvisasponsors.com/jobs", timeout=30000)
    await page.wait_for_load_state('networkidle', timeout=30000)
    await asyncio.sleep(10)  # Wait longer to avoid rate limiting
    
    # Build URL with query parameters
    base_url = "https://api.huntukvisasponsors.com/api/v1/search/jobs/facets"
    params = {
        "search": "ServiceNow",
        "location": "United Kingdom",
        "limit": 50,
    }
    url = f"{base_url}?{'&'.join([f'{k}={v}' for k, v in params.items()])}"
    
    try:
        print(f"Requesting: {url}")
        response = await page.goto(url, timeout=30000)
        if response:
            status = response.status
            print(f"Status: {status}")
            if status == 200:
                body = await response.text()
                try:
                    json_data = json.loads(body)
                    print(f"JSON keys: {list(json_data.keys())}")
                    if 'jobs' in json_data:
                        print(f"Found {len(json_data['jobs'])} jobs")
                        for job in json_data['jobs'][:3]:
                            print(f"  - {job.get('title', 'N/A')}")
                except json.JSONDecodeError:
                    print(f"Body: {body[:500]}...")
            else:
                body = await response.text()
                print(f"Error: {body[:500]}")
        else:
            print("No response")
    except Exception as e:
        print(f"Error: {e}")
        
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())