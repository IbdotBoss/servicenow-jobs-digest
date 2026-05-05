#!/usr/bin/env python3
"""
Capture network requests while scrolling to find job API endpoint
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
        if len(requests) >= 50:
            page.remove_listener("request", handle_request)
    
    page.on("request", handle_request)
    
    print("Navigating to Hunt UK jobs page...")
    await page.goto("https://huntukvisasponsors.com/jobs", timeout=30000)
    await page.wait_for_load_state('networkidle', timeout=30000)
    await asyncio.sleep(5)
    
    print("Scrolling to load more content...")
    for i in range(3):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
    
    print(f"\nCaptured {len(requests)} requests")
    
    # Look for JSON responses
    json_requests = []
    for request in requests[-20:]:
        try:
            response = await request.response()
            if response:
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    body = await response.body()
                    try:
                        json_data = json.loads(body)
                        json_requests.append({
                            'url': request.url,
                            'method': request.method,
                            'json': json_data
                        })
                    except:
                        pass
        except:
            continue
            
    print(f"\nFound {len(json_requests)} JSON responses:")
    for i, req in enumerate(json_requests[:5]):
        print(f"\n{i+1}. {req['method']} {req['url']}")
        print(f"   JSON preview: {json.dumps(req['json'], indent=2)[:200]}...")
        
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())