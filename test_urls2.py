#!/usr/bin/env python3
"""
Test different URLs to find the jobs API endpoint
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
    
    # Test different URLs
    test_urls = [
        "https://huntukvisasponsors.com/jobs",
        "https://huntukvisasponsors.com/api/jobs",
        "https://huntukvisasponsors.com/graphql",
        "https://huntukvisasponsors.com/jobs/role",
        "https://huntukvisasponsors.com/jobs/role/software-engineer",
    ]
    
    for url in test_urls:
        try:
            print(f"\nTesting URL: {url}")
            await page.goto(url, timeout=30000)
            await page.wait_for_load_state('networkidle', timeout=30000)
            await asyncio.sleep(5)
            
            # Get all requests made by the page
            print("  Network requests:")
            requests = []
            async for request in page:
                requests.append(request)
                if len(requests) >= 10:
                    break
                    
            for request in requests[-10:]:
                print(f"    {request.method} {request.url}")
                
        except Exception as e:
            print(f"  Error: {e}")
            
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())