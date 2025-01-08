from typing import Optional, Dict, List
from playwright.async_api import async_playwright, Browser, Page
from abc import ABC
import logging
from datetime import datetime
from tools.base import Tool
from config import CONFIG

isu_booking_creds = CONFIG.isu_booking_creds

logger = logging.getLogger(__name__)


class BrowserTool(Tool):
    def __init__(self):
        self.page: Optional[Page] = None
        self._browser: Optional[Browser] = None

    async def _ensure_browser(self):
        if not self._browser:
            playwright = await async_playwright().start()
            self._browser = await playwright.chromium.launch(
                headless=True,
                args=['--no-sandbox', '--disable-setuid-sandbox']
            )
            self.page = await self._browser.new_page()
            # Add debug logging
            self.page.on("console", lambda msg: logger.debug(
                f"Browser console: {msg.text}"))


class LoginTool(BrowserTool):
    async def execute(
        self,
        login_url: str = isu_booking_creds.booking_login,
        password: str = isu_booking_creds.password,
        username: str = isu_booking_creds.username,
    ) -> Dict:
        await self._ensure_browser()
        try:
            logger.debug(f"Navigating to %s", login_url)
            await self.page.goto(login_url, timeout=4000)

            logger.debug("Waiting for login form")
            await self.page.wait_for_selector('#username', timeout=4000)
            await self.page.fill('#username', username)
            await self.page.fill('#password', password)

            logger.debug("Clicking login button")
            async with self.page.expect_navigation(timeout=10000):
                await self.page.click('#kc-login', timeout=4000)

            logger.debug("Verifying login success")
            success = await self._verify_login()

            current_url = self.page.url
            logger.debug(f"Current URL after login: {current_url}")

            return {
                'success': success,
                'current_url': current_url
            }
        except Exception as e:
            logger.error(f"Login failed: {str(e)}")
            return {'success': False, 'error': str(e)}

    async def _verify_login(self) -> bool:
        """
        Verify login success by checking multiple conditions:
        - presence of navbar search
        - presence of main menu
        - presence of specific text elements
        Returns True if any condition is met
        """
        try:
            # Check for UI elements
            navbar_exists = await self.page.is_visible('.navbar-search')
            menu_exists = await self.page.is_visible('#main-menu-inner')

            # Check for specific text content
            expected_texts = ["Личный кабинет", "Центр приложений"]
            content = await self.page.content()
            text_found = any(text in content for text in expected_texts)

            success = any([navbar_exists, menu_exists, text_found])

            # Log which conditions were met
            logger.debug(f"Login verification results: \n"
                         f"- Navbar found: {navbar_exists}\n"
                         f"- Menu found: {menu_exists}\n"
                         f"- Expected text found: {text_found}")

            return success

        except Exception as e:
            logger.error(f"Login verification failed: {str(e)}")
            return False

    def description(self) -> str:
        return "Handles login to the ISU booking system"
