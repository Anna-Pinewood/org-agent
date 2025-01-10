from tools.base import Tool
from .manager import BrowserManager
from playwright.async_api import Page

class BrowserTool(Tool):
    """Base class for browser-based tools"""

    def __init__(self):
        self.browser_manager = BrowserManager()

    async def _get_page(self) -> Page:
        """Get the shared page instance"""
        return await self.browser_manager.get_page()
