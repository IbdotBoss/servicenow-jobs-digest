#!/usr/bin/env python3
"""
Scroll page to see if job listings appear
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
    
    await page.goto("https://huntukvisasponsors.com/jobs", timeout=30000)
    await page.wait_for_load_state('networkidle', timeout=30000)
    await asyncio.sleep(5)
    
    # Scroll down multiple times
    for i in range(3):
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight / 2)")
        await asyncio.sleep(2)
        await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        await asyncio.sleep(2)
    
    # Get page content
    content = await page.content()
    print(f"Page content length after scrolling: {len(content)}")
    
    # Look for job-related keywords
    keywords = ['job', 'vacancy', 'career', 'apply']
    content_lower = content.lower()
    for keyword in keywords:
        count = content_lower.count(keyword)
        print(f"  '{keyword}' appears {count} times")
        
    await browser.close()
    await playwright.stop()

if __name__ == "__main__":
    asyncio.run(main())