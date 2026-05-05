#!/usr/bin/env python3
"""
Inspect HTML structure of job sites
"""

import asyncio
from playwright.async_api import async_playwright
import requests
from bs4 import BeautifulSoup
import re

async def inspect_site(name, url):
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
        print(f"\n=== {name} ({url}) ===")
        await page.goto(url, timeout=30000)
        await page.wait_for_load_state('networkidle', timeout=30000)
        await asyncio.sleep(5)
        
        content = await page.content()
        soup = BeautifulSoup(content, 'html.parser')
        
        # Look for search input fields
        inputs = soup.find_all(['input', 'select', 'textarea'])
        print(f"Found {len(inputs)} input elements")
        for i, inp in enumerate(inputs[:10]):
            print(f"  {i+1}. type={inp.get('type', 'N/A')}, id={inp.get('id', 'N/A')}, name={inp.get('name', 'N/A')}, class={inp.get('class', [])}")
            
        # Look for search forms
        forms = soup.find_all('form')
        print(f"Found {len(forms)} forms")
        for i, form in enumerate(forms[:3]):
            action = form.get('action', '')
            method = form.get('method', 'GET')
            print(f"  Form {i+1}: action={action}, method={method}")
            for inp in form.find_all(['input', 'select', 'textarea'])[:3]:
                print(f"    - {inp.get('type', 'N/A')}: {inp.get('name', 'N/A')}")
                
        # Look for job cards
        job_cards = soup.find_all(['div', 'article'], class_=re.compile(r'job|vacancy|career', re.I))
        print(f"Found {len(job_cards)} potential job cards")
        for i, card in enumerate(job_cards[:3]):
            print(f"  Card {i+1}: classes={card.get('class', [])}")
            if card.get('class'):
                print(f"    Class string: {card.get('class')}")
            print(f"    Text preview: {card.text.strip()[:200]}...")
            
    except Exception as e:
        print(f"Error inspecting {name}: {e}")
    finally:
        await browser.close()
        await playwright.stop()

async def main():
    sites = [
        ("Indeed", "https://www.indeed.com/jobs"),
        ("Reed", "https://www.reed.co.uk/jobs"),
        ("Totaljobs", "https://www.totaljobs.com"),
    ]
    
    for name, url in sites:
        await inspect_site(name, url)
        await asyncio.sleep(2)

if __name__ == "__main__":
    asyncio.run(main())