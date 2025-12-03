"""Playwright MCP Server for visual verification."""

from __future__ import annotations

import asyncio
import base64
from typing import Any, Callable, Dict, List, Optional
from playwright.async_api import async_playwright

class PlaywrightMCPServer:
    """
    MCP Server for visual verification using Playwright.
    Provides tools for taking screenshots and checking layouts.
    """
    
    def __init__(self):
        self._browser = None
        self._context = None
        
    async def start(self):
        """Start the browser session."""
        self._playwright = await async_playwright().start()
        self._browser = await self._playwright.chromium.launch(headless=True)
        self._context = await self._browser.new_context()
        
    async def stop(self):
        """Stop the browser session."""
        if self._context:
            await self._context.close()
        if self._browser:
            await self._browser.close()
        if hasattr(self, '_playwright'):
            await self._playwright.stop()
            
    async def take_screenshot(self, url: str, output_path: str, full_page: bool = False) -> str:
        """
        Take a screenshot of a webpage.
        
        Args:
            url: The URL to visit.
            output_path: Where to save the screenshot.
            full_page: Whether to capture the full scrollable page.
            
        Returns:
            Status message.
        """
        if not self._browser:
            await self.start()
            
        page = await self._context.new_page()
        try:
            await page.goto(url)
            await page.screenshot(path=output_path, full_page=full_page)
            return f"Screenshot saved to {output_path}"
        finally:
            await page.close()
            
    def get_tools(self) -> List[Callable]:
        """Return list of callable tools."""
        return [
            self.take_screenshot
        ]

