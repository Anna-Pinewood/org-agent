from typing import Dict, Optional, List
import logging
from datetime import datetime
from dataclasses import dataclass
from bs4 import BeautifulSoup
from playwright.async_api import (
    async_playwright, Browser, Page,
    BrowserContext, Request, Response
)
from config import CONFIG

TIMEOUT = CONFIG.isu_booking_creds.page_interaction_timeout
logger = logging.getLogger(__name__)


@dataclass
class RequestResponsePair:
    """Pairs a request with its corresponding response and tracks errors"""
    request: Request
    response: Optional[Response] = None
    error: Optional[str] = None
    timestamp: datetime = datetime.now()


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

    # Request tracking
    _request_pairs: Dict[str, RequestResponsePair] = {}
    _request_order: List[str] = []
    _max_entries: int = 1000

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

            # Set up logging and tracking
            self._page.on("console", lambda msg: logger.debug(
                "Browser console: %s", msg.text))
            self._setup_tracking()

    def _setup_tracking(self) -> None:
        """Set up event listeners for request/response tracking"""
        if not self._page:
            raise RuntimeError("Page not initialized")

        async def on_request(request: Request):
            try:
                self._request_pairs[request.url] = RequestResponsePair(
                    request=request)
                self._request_order.append(request.url)
                self._prune_old_entries()
                logger.debug("Tracking request to %s", request.url)
            except Exception as e:
                logger.error("Failed to track request: %s", str(e))

        async def on_response(response: Response):
            try:
                if response.request.url in self._request_pairs:
                    self._request_pairs[response.request.url].response = response
                    logger.debug(
                        "Recorded response from %s (status %d)",
                        response.url, response.status
                    )
            except Exception as e:
                logger.error("Failed to track response: %s", str(e))

        async def on_request_failed(request: Request):
            try:
                if request.url in self._request_pairs:
                    self._request_pairs[request.url].error = f"Request failed: {request.failure}"
                    logger.debug("Recorded failed request to %s", request.url)
            except Exception as e:
                logger.error("Failed to track request failure: %s", str(e))

        self._page.on("request", on_request)
        self._page.on("response", on_response)
        self._page.on("requestfailed", on_request_failed)

    def _prune_old_entries(self) -> None:
        """Remove oldest entries when max_entries is exceeded"""
        while len(self._request_order) > self._max_entries:
            url = self._request_order.pop(0)
            del self._request_pairs[url]
            logger.debug("Pruned old request entry: %s", url)

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

    async def navigate(self, url: str, timeout: int = TIMEOUT) -> None:
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

    def get_recent_requests(self, count: int = 10) -> List[RequestResponsePair]:
        """Get most recent request/response pairs"""
        return [self._request_pairs[url] for url in self._request_order[-count:]]

    def get_failed_requests(self) -> List[RequestResponsePair]:
        """Get all requests that resulted in errors or non-200 responses"""
        failed = []
        for pair in self._request_pairs.values():
            if pair.error or (pair.response and pair.response.status >= 400):
                failed.append(pair)
        return failed
