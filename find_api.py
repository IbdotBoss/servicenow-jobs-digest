#!/usr/bin/env python3
"""
Network Monitor for Hunt UK to find API endpoint
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
    
    requests = []
    
    def handle_request(request):
        requests.append(request)
        if len(requests) >= 20:
            page.remove_listener("request", handle_request)
    
    page.on("request", handle_request)
    
    print("Navigating to Hunt UK jobs page...")
    await page.goto("https://huntukvisasponsors.com/jobs", timeout=30000)
    await page.wait_for_load_state('networkidle', timeout=30000)
    await asyncio.sleep(5)
    
    print("\n=== Captured Network Requests ===")
    for request in requests[-20:]:
        try:
            response = await request.response()
            if response:
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    body = await response.body()
                    try:
                        json_data = json.loads(body)
                        print(f"\n🔴 {request.method} {request.url}")
                        print(f"    JSON data: {json.dumps(json_data, indent=2)[:200]}...")
                    except:
                        pass
                else:
                    print(f"    {request.method} {request.url}")
            else:
                print(f"    {request.method} {request.url}")
        except:
            continue
            
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())