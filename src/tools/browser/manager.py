from typing import Optional
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
import logging

logger = logging.getLogger(__name__)

class BrowserManager:
    """
    Singleton class to manage browser instance and context.
    Ensures only one browser instance is created and shared across all tools.
    """
    _instance = None
    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None
    _page: Optional[Page] = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserManager, cls).__new__(cls)
        return cls._instance

    async def ensure_browser(self):
        """Ensure browser, context and page are initialized"""
        if not self._browser:
            logger.info("Starting new browser instance")
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()

            # Add debug logging
            self._page.on("console", lambda msg: logger.debug(
                "Browser console: %s", msg.text))

    async def get_page(self) -> Page:
        """Get the current page, ensuring browser is initialized"""
        await self.ensure_browser()
        return self._page

    async def close(self):
        """Close browser and clean up resources"""
        if self._browser:
            await self._browser.close()
            self._browser = None
            self._context = None
            self._page = None
