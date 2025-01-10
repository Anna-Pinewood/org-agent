from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, Page, BrowserContext
from abc import ABC
import logging
from datetime import datetime
from tools.base import Tool
from config import CONFIG

isu_booking_creds = CONFIG.isu_booking_creds
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
            logger.debug("Starting new browser instance")
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


class BrowserTool(Tool):
    """Base class for browser-based tools"""

    def __init__(self):
        self.browser_manager = BrowserManager()

    async def _get_page(self) -> Page:
        """Get the shared page instance"""
        return await self.browser_manager.get_page()


class LoginTool(BrowserTool):
    """Tool for handling login operations"""

    async def execute(
        self,
        login_url: str = isu_booking_creds.booking_login,
        password: str = isu_booking_creds.password,
        username: str = isu_booking_creds.username,
        timeout: int = isu_booking_creds.page_interaction_timeout
    ) -> Dict:
        """
        Execute login sequence

        Args:
            login_url: URL of the login page
            password: User's password
            username: User's username
            timeout: Timeout for page interactions in milliseconds

        Returns:
            Dict containing:
                - success: bool indicating if login was successful
                - current_url: str with current page URL
                - error: str with error message if login failed
        """
        try:
            page = await self._get_page()

            logger.debug("Navigating to %s", login_url)
            await page.goto(login_url, timeout=timeout)

            logger.debug("Waiting for login form")
            await page.wait_for_selector('#username', timeout=timeout)
            await page.fill('#username', username)
            await page.fill('#password', password)

            logger.debug("Clicking login button")
            async with page.expect_navigation(timeout=timeout):
                await page.click('#kc-login', timeout=timeout)

            logger.debug("Verifying login success")
            success = await self._verify_login(page)

            current_url = page.url
            logger.debug("Current URL after login: %s", current_url)

            # Debug session information
            cookies = await page.context.cookies()
            logger.debug("Cookies after login: %s", cookies)

            storage = await page.evaluate("() => Object.entries(localStorage)")
            logger.debug("Local storage: %s", storage)

            return {
                'success': success,
                'current_url': current_url
            }
        except Exception as e:
            logger.error("Login failed: %s", str(e))
            return {'success': False, 'error': str(e)}

    async def _verify_login(self, page: Page) -> bool:
        """
        Verify login success by checking multiple conditions

        Args:
            page: Page instance to check

        Returns:
            bool: True if any success condition is met
        """
        try:
            navbar_exists = await page.is_visible('.navbar-search')
            menu_exists = await page.is_visible('#main-menu-inner')

            expected_texts = ["Личный кабинет", "Центр приложений"]
            content = await page.content()
            text_found = any(text in content for text in expected_texts)

            success = any([navbar_exists, menu_exists, text_found])

            logger.debug(
                "Login verification results: \n"
                "- Navbar found: %s\n"
                "- Menu found: %s\n"
                "- Expected text found: %s",
                navbar_exists, menu_exists, text_found
            )

            return success

        except Exception as e:
            logger.error("Login verification failed: %s", str(e))
            return False

    def description(self) -> str:
        return "Handles login to the ISU booking system"


class BookingPageTool(BrowserTool):
    """Tool for checking and navigating to the booking page"""

    async def execute(
        self,
        booking_url: str = isu_booking_creds.booking_address,
        timeout: int = isu_booking_creds.page_interaction_timeout
    ) -> Dict:
        """
        Navigate to booking page and check its status

        Args:
            booking_url: URL of the booking page
            timeout: Timeout for page interactions in milliseconds

        Returns:
            Dict with fields:
                - status: str ('logged_in', 'login_required', 'unknown', or 'error')
                - current_url: str (current page URL)
                - error: str (if any error occurred)
        """
        try:
            page = await self._get_page()

            logger.debug("Navigating to booking page: %s", booking_url)
            await page.goto(booking_url, timeout=timeout)

            # Check for login page indicators
            login_indicators = ["Войти с помощью",
                                "Еще нет учетной записи?", "Регистрация"]
            logged_in_indicators = [
                "Бронирование помещений", "Мои заявки", "Создать заявку"]

            content = await page.content()

            # Check if we're on login page
            needs_login = any(
                indicator in content for indicator in login_indicators)
            is_logged_in = any(
                indicator in content for indicator in logged_in_indicators)

            logger.debug(
                "Page status check - needs login: %s, is logged in: %s",
                needs_login, is_logged_in
            )

            current_url = page.url

            # Debug session information
            cookies = await page.context.cookies()
            logger.debug("Cookies for booking page: %s", cookies)

            if needs_login:
                return {
                    'status': 'login_required',
                    'current_url': current_url
                }
            elif is_logged_in:
                return {
                    'status': 'logged_in',
                    'current_url': current_url
                }
            else:
                logger.warning("Unable to determine page status")
                return {
                    'status': 'unknown',
                    'current_url': current_url,
                    'error': 'Could not determine page status'
                }

        except Exception as e:
            logger.error("Error checking booking page: %s", str(e))
            return {
                'status': 'error',
                'error': str(e)
            }

    def description(self) -> str:
        return "Checks booking page status and determines if login is required"
