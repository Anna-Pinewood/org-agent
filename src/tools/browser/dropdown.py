import logging
from typing import Optional
from src.config import CONFIG
from src.tools.base import ToolResponse
from src.tools.browser.base import BrowserTool
from src.tools.browser.environment import BrowserEnvironment

logger = logging.getLogger(__name__)

TIMEOUT = CONFIG.isu_booking_creds.page_interaction_timeout


class DropDownTool(BrowserTool):
    """Atomic tool for interacting with dropdown/select elements"""

    async def execute(
        self,
        env: BrowserEnvironment,
        option_text: str,
        dropdown_selector: str = None,
        dropdown_text: str = None,
        timeout: int = TIMEOUT,
    ) -> ToolResponse:
        """Select an option from a dropdown menu

        Parameters
        ----------
        env : BrowserEnvironment
            Browser environment instance
        option_text : str
            Text of the option to select
        dropdown_selector : str, optional
            CSS selector for the dropdown element
        dropdown_text : str, optional
            Text to identify the dropdown element
        verify_selector : str, optional
            Selector to verify selected value (e.g., '.selected-value')
        timeout : int, optional
            Maximum wait time in ms
        """
        meta = {
            "action": "select_dropdown",
            "target": dropdown_selector or f"text='{dropdown_text}'",
            "option": option_text,
            "url": env.page.url,
            "narrative": []
        }

        if not dropdown_selector and not dropdown_text:
            msg = "Must provide either dropdown_selector or dropdown_text"
            meta["narrative"].append(msg)
            logger.error(msg)
            return ToolResponse(
                success=False,
                error=msg,
                meta=meta
            )

        try:
            # Click the dropdown to open it
            if dropdown_selector:
                msg = f"Clicking dropdown by selector: {dropdown_selector}"
                meta["narrative"].append(msg)
                logger.info(msg)
                await env.page.click(dropdown_selector, timeout=timeout)
            else:
                msg = f"Clicking dropdown with text: {dropdown_text}"
                meta["narrative"].append(msg)
                logger.info(msg)
                await env.page.get_by_text(dropdown_text).click(timeout=timeout)

            # Select the option
            msg = f"Selecting option: {option_text}"
            meta["narrative"].append(msg)
            logger.info(msg)
            await env.page.get_by_role("option", name=option_text).click(timeout=timeout)

            msg = f"Successfully selected '{option_text}' from dropdown"
            meta["narrative"].append(msg)
            logger.info(msg)

            return ToolResponse(
                success=True,
                meta=meta
            )

        except Exception as e:
            page_content = await env.page.content()
            error_msg = f"Dropdown selection failed: {str(e)}"
            meta["narrative"].append(error_msg)
            meta["narrative"].append(f"Page content:\n{page_content}")
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                error=error_msg,
                meta=meta
            )

    def description(self):
        return """Playwright tool for interacting with dropdown/select elements.
        Parameters:
        option_text: str - Text of the option to select
        dropdown_selector: str | None - CSS selector for the dropdown element
        dropdown_text: str | None - Text to identify the dropdown element
        timeout: int - Maximum wait time in milliseconds
        
        Can use either dropdown_selector or dropdown_text to identify the dropdown.
        """


class DropdownOptionsTool(BrowserTool):
    """Tool for extracting options from a dropdown/select element"""

    async def execute(
        self,
        env: BrowserEnvironment,
        dropdown_selector: str = None,
        dropdown_text: str = None,
        timeout: int = TIMEOUT,
    ) -> ToolResponse:
        """Get all options from a dropdown menu and restore dropdown state

        Parameters
        ----------
        env : BrowserEnvironment
            Browser environment instance
        dropdown_selector : str, optional
            CSS selector for the dropdown element
        dropdown_text : str, optional
            Text to identify the dropdown element
        timeout : int, optional
            Maximum wait time in ms
        """
        meta = {
            "action": "get_dropdown_options",
            "target": dropdown_selector or f"text='{dropdown_text}'",
            "url": env.page.url,
            "narrative": []
        }

        if not dropdown_selector and not dropdown_text:
            msg = "Must provide either dropdown_selector or dropdown_text"
            meta["narrative"].append(msg)
            logger.error(msg)
            return ToolResponse(
                success=False,
                error=msg,
                meta=meta
            )

        try:
            # Click to open dropdown
            if dropdown_selector:
                msg = f"Opening dropdown by selector: {dropdown_selector}"
                meta["narrative"].append(msg)
                logger.info(msg)
                await env.page.click(dropdown_selector, timeout=timeout)
            else:
                msg = f"Opening dropdown with text: {dropdown_text}"
                meta["narrative"].append(msg)
                logger.info(msg)
                await env.page.get_by_text(dropdown_text).click(timeout=timeout)

            # Get all options
            msg = "Retrieving dropdown options"
            meta["narrative"].append(msg)
            logger.info(msg)
            options = await env.page.locator('role=option').all_text_contents()
            meta["options"] = options

            # Press Escape to close dropdown
            msg = "Closing dropdown with Escape key"
            meta["narrative"].append(msg)
            logger.info(msg)
            await env.page.keyboard.press('Escape')

            msg = f"Successfully retrieved {len(options)} options"
            meta["narrative"].append(msg)
            logger.info(msg)

            return ToolResponse(
                success=True,
                data=options,
                meta=meta
            )

        except Exception as e:
            page_content = await env.page.content()
            error_msg = f"Getting dropdown options failed: {str(e)}"
            meta["narrative"].append(error_msg)
            meta["narrative"].append(f"Page content:\n{page_content}")
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                error=error_msg,
                meta=meta
            )

    def description(self):
        return """Playwright tool for getting all options from a dropdown/select element.
        Parameters:
        dropdown_selector: str | None - CSS selector for the dropdown element
        dropdown_text: str | None - Text to identify the dropdown element
        
        Returns list of available options as strings.
        Can use either dropdown_selector or dropdown_text to identify the dropdown.
        """

# Test code for notebook
