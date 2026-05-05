#!/usr/bin/env python3
"""
Debug script to save page source
"""

import asyncio
from playwright.async_api import async_playwright

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
    
    # Navigate to Hunt UK site
    await page.goto("https://huntukvisasponsors.com/jobs", timeout=30000)
    
    # Wait for page to load
    await page.wait_for_load_state('networkidle', timeout=30000)
    
    # Wait a bit more
    await asyncio.sleep(5)
    
    # Get page content
    content = await page.content()
    
    # Save to file
    with open('page_source.html', 'w', encoding='utf-8') as f:
        f.write(content)
        
    print("Page source saved to page_source.html")
    
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())