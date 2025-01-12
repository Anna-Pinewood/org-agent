from typing import Dict, Optional
import logging
from bs4 import BeautifulSoup
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from config import CONFIG

TIMEOUT = CONFIG.isu_booking_creds.page_interaction_timeout
logger = logging.getLogger(__name__)


class BrowserEnvironment:
    """
    Manages browser state and provides controlled access to the browser.
    Acts as a singleton to maintain consistent state across the application.
    """
    _instance = None
    _browser: Optional[Browser] = None
    _context: Optional[BrowserContext] = None
    _page: Optional[Page] = None
    _current_url: str = ""

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(BrowserEnvironment, cls).__new__(cls)
        return cls._instance

    async def initialize(self):
        """Initialize browser environment if not already running"""
        if not self._browser:
            logger.info("Starting new browser environment")
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self._context = await self._browser.new_context()
            self._page = await self._context.new_page()

            # Set up logging
            self._page.on("console", lambda msg: logger.debug(
                "Browser console: %s", msg.text))

    @property
    def page(self) -> Page:
        """Get current page - environment must be initialized first"""
        if not self._page:
            raise RuntimeError("Browser environment not initialized")
        return self._page

    @property
    def current_url(self) -> str:
        """Get current page URL"""
        return self._current_url if self._page else ""

    async def navigate(
            self, url: str,
            timeout: int = TIMEOUT) -> None:
        """Navigate to URL and update current_url"""
        await self.page.goto(url, timeout=timeout)
        self._current_url = self.page.url

    async def describe_state(self) -> str:
        """Get concise description of browser state"""
        page_content = await self.page.content()
        soup = BeautifulSoup(page_content, 'html.parser')
        headers = []
        for header_tag in ['h1', 'h2', 'h3', 'h4']:
            for header in soup.find_all(header_tag):
                headers.append(header.get_text(strip=True))
        return "\n".join(headers)
