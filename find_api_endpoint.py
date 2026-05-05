#!/usr/bin/env python3
"""
Find API endpoint by capturing network responses while scrolling
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
    
    try:
        await page.goto("https://www.reed.co.uk/jobs", timeout=30000)
        await page.wait_for_load_state('networkidle', timeout=30000)
        await asyncio.sleep(5)
        
        # Scroll and capture responses
        responses = []
        
        async def handle_response(response):
            try:
                content_type = response.headers.get('content-type', '')
                if 'application/json' in content_type:
                    body = await response.body()
                    try:
                        json_data = json.loads(body)
                        responses.append({
                            'url': response.request().url,
                            'method': response.request().method,
                            'json': json_data
                        })
                    except:
                        pass
            except:
                pass
        
        page.on("response", handle_response)
        
        # Scroll multiple times
        for _ in range(5):
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
            await asyncio.sleep(2)
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await asyncio.sleep(2)
        
        await asyncio.sleep(5)  # Wait for any remaining requests
        
        print(f"Captured {len(responses)} JSON responses:")
        for resp in responses[:5]:
            print(f"\nURL: {resp['url']}")
            print(f"Method: {resp['method']}")
            print(f"JSON preview: {json.dumps(resp['json'], indent=2)[:200]}...")
            
    except Exception as e:
        print(f"Error: {e}")
    finally:
        await browser.close()
        await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())