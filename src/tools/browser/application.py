from typing import Dict
import logging
from playwright.async_api import Page
from .base import BrowserTool
from src.config import CONFIG

logger = logging.getLogger(__name__)


class BookAppButton(BrowserTool):
    """Tool for navigating to the booking creation form"""

    async def execute(
        self,
        timeout: int = CONFIG.isu_booking_creds.page_interaction_timeout
    ) -> Dict:
        """
        Click the 'Создать заявку' button to navigate to booking form

        Returns:
            Dict containing:
                - success: bool indicating if navigation was successful
                - error: str with error message if navigation failed
        """
        try:
            page = await self._get_page()
            await page.goto(CONFIG.isu_booking_creds.booking_url, timeout=timeout)

            # Find and click the "Создать заявку" button by its text content
            logger.info("Looking for 'Создать заявку' button")
            button = await page.get_by_role(
                "button",
                name="Создать заявку"
            ).click(timeout=timeout)

            # Wait for navigation to complete after button click
            await page.wait_for_load_state('networkidle', timeout=timeout)

            # Verify we're on the correct page
            verify_result = await self._verify_transition(page, timeout)
            if not verify_result['success']:
                return verify_result

            current_url = page.url
            logger.info(
                "Successfully navigated to booking form at: %s", current_url)

            return {
                'success': True,
                'current_url': current_url
            }

        except Exception as e:
            logger.error("Failed to navigate to booking form: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }

    def description(self) -> str:
        return "Navigates to the booking creation form by clicking 'Создать заявку'"

    async def _verify_transition(self, page: Page, timeout: int) -> Dict:
        """Verify that transition to booking form was successful by checking for expected text markers"""
        try:
            expected_texts = [
                "Карточка заявки",
                "Заявка",
                "Картотека заявок",
                "Проект заявки"
            ]

            # Wait for page content to be available
            content = await page.content()

            # Check for presence of all required texts
            expected_texts_found = {text: False for text in expected_texts}
            for text in expected_texts:
                if text in content:
                    expected_texts_found[text] = True

            if not all(expected_texts_found.values()):
                logger.error(
                    "Missing required texts on page:\n%s", expected_texts_found)
                return {
                    'success': False,
                    'error': f"Page verification failed - missing texts:\n{expected_texts_found}"
                }

            logger.info(
                "Successfully verified booking form page:\n%s", expected_texts_found)
            return {'success': True}
        except Exception as e:
            logger.error("Page content verification failed: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }


class SelectBuildingTool(BrowserTool):
    """Tool for selecting a building from the dropdown list"""

    async def _verify_select(
            self, page: Page,
            expected_building: str, timeout: int) -> Dict:
        """
        Verify that the correct building was selected by checking the select2-chosen span

        Args:
            page: Playwright page object
            expected_building: The building name that should be selected
            timeout: Timeout for page interactions in milliseconds

        Returns:
            Dict containing verification result and details
        """
        try:
            # Wait for select2-chosen span to update
            await page.wait_for_selector('.select2-chosen', timeout=timeout)

            # Get the selected value from span
            selected_text = await page.locator('.select2-chosen').text_content()

            if selected_text != expected_building:
                logger.error("Building selection mismatch - Expected: %s, Got: %s",
                             expected_building, selected_text)
                return {
                    'success': False,
                    'error': f"Building selection verification failed - selected '{selected_text}' instead of '{expected_building}'"
                }

            logger.info(
                "Successfully verified building selection: %s", selected_text)
            return {
                'success': True,
                'selected_building': selected_text
            }

        except Exception as e:
            logger.error("Building selection verification failed: %s", str(e))
            return {
                'success': False,
                'error': str(e)
            }

    async def execute(
        self,
        building: str,
        application_url: str,
        timeout: int = CONFIG.isu_booking_creds.page_interaction_timeout
    ) -> Dict:
        """
        Select the specified building from the dropdown and verify selection

        Args:
            building: Name of the building to select (e.g. "ITMO PLACE (Ломоносова 9)")
            timeout: Timeout for page interactions in milliseconds

        Returns:
            Dict containing:
                - success: bool indicating if building was selected and verified
                - selected_building: str name of the selected building if successful
                - error: str with error message if selection failed
        """
        try:
            page = await self._get_page()
            await page.goto(application_url, timeout=timeout)
            logger.info("Looking for building selection dropdown")

            # Wait for and click the building selection dropdown
            await page.locator(".select2-choice").click(timeout=timeout)

            logger.info("Attempting to select building: %s", building)
            await page.get_by_role(
                "option",
                name=building
            ).click(timeout=timeout)

            # Verify selection was successful
            verify_result = await self._verify_select(page, building, timeout)
            if not verify_result['success']:
                return verify_result

            logger.info(
                "Building selection completed successfully: %s", building)
            return verify_result

        except Exception as e:
            logger.error("Failed to select building '%s': %s",
                         building, str(e))
            return {
                'success': False,
                'error': str(e)
            }

    def description(self) -> str:
        return "Selects a specified building from the booking form dropdown"
