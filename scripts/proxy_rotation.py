#!/usr/bin/env python3
"""Utility for proxy rotation for Playwright scrapers"""

import asyncio
import random
from typing import List, Optional

class ProxyRotator:
    def __init__(self, proxy_list: List[str] = None):
        self.proxy_list = proxy_list or []
        self.current_index = 0
    
    def get_proxy(self) -> Optional[str]:
        if not self.proxy_list:
            return None
        proxy = self.proxy_list[self.current_index]
        self.current_index = (self.current_index + 1) % len(self.proxy_list)
        return proxy

async def with_proxy_rotation(scraper_class, proxy_list: List[str] = None):
        """Decorator function to add proxy rotation to a scraper."""
        original_initialize = scraper_class.initialize
        
        async def patched_initialize(self):
            self.playwright = await async_playwright().start()
            proxy = proxy_list[0] if proxy_list else None
            self.browser = await self.playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-dev-shm-usage'],
                proxy={"server": proxy} if proxy else None
            )
            self.context = await self.browser.new_context(
                viewport={'width': 1920, 'height': 1080}
            )
            self.page = await self.context.new_page()
        
        scraper_class.initialize = patched_initialize
        
        # Create instance and run
        scraper = scraper_class()
        result = await scraper.run()
        return result

