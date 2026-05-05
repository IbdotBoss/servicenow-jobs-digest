#!/usr/bin/env python3
"""
Capture all network responses from Hunt UK for analysis
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
    
    responses = []
    
    def handle_response(response):
        asyncio.create_task(process_response(response))
        
    async def process_response(response):
        try:
            request = await response.request()
            url = request.url
            method = request.method
            
            # Only capture JSON responses
            content_type = response.headers.get('content-type', '')
            if 'application/json' in content_type:
                body = await response.body()
                try:
                    json_data = json.loads(body)
                    responses.append({
                        'url': url,
                        'method': method,
                        'json': json_data
                    })
                except:
                    pass
        except:
            pass
            
    page.on("response", handle_response)
    
    print("Navigating to Hunt UK jobs page...")
    await page.goto("https://huntukvisasponsors.com/jobs", timeout=30000)
    await page.wait_for_load_state('networkidle', timeout=30000)
    await asyncio.sleep(5)
    
    print(f"\nCaptured {len(responses)} JSON responses")
    for i, resp in enumerate(responses[:5]):
        print(f"\nResponse {i+1}:")
        print(f"  URL: {resp['url']}")
        print(f"  Method: {resp['method']}")
        print(f"  JSON preview: {json.dumps(resp['json'], indent=2)[:200]}...")
        
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())