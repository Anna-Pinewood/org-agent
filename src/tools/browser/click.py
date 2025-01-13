import logging
from typing import Optional
from src.config import CONFIG
from src.tools.base import ToolResponse
from src.tools.browser.base import BrowserTool
from src.tools.browser.environment import BrowserEnvironment

logger = logging.getLogger(__name__)

TIMEOUT = CONFIG.isu_booking_creds.page_interaction_timeout


class ClickTool(BrowserTool):
    """Atomic tool for clicking elements with navigation handling"""

    async def execute(
        self,
        env: BrowserEnvironment,
        selector: Optional[str] = None,
        text: Optional[str] = None,
        timeout: int = TIMEOUT,
        wait_for_navigation: bool = True,
    ) -> ToolResponse:
        """Click element and optionally wait for navigation

        Parameters
        ----------
        env : BrowserEnvironment
        selector : Optional[str]
            CSS selector of element to click
        text : Optional[str] 
            Text of element to click
        timeout : int, optional
            Maximum wait time in ms
        wait_for_navigation : bool, optional
            Whether to wait for page load after click
        """
        meta = {
            "action": "click",
            "target": selector or f"text='{text}'",
            "url": env.page.url,
            "narrative": []
        }

        if not selector and not text:
            msg = "Must provide either selector or text"
            meta["narrative"].append(msg)
            logger.error(msg)
            return ToolResponse(
                success=False,
                error=msg,
                meta=meta
            )

        try:
            if wait_for_navigation:
                async with env.page.expect_navigation(timeout=timeout):
                    if selector:
                        msg = f"Attempting to click element by selector: {selector}"
                        meta["narrative"].append(msg)
                        logger.info(msg)
                        await env.page.click(selector, timeout=timeout)
                    else:
                        msg = f"Attempting to click button with text: {text}"
                        meta["narrative"].append(msg)
                        logger.info(msg)
                        await env.page.get_by_role("button", name=text).click(timeout=timeout)

                msg = "Waiting for navigation to complete"
                meta["narrative"].append(msg)
                logger.info(msg)
                await env.page.wait_for_load_state('networkidle')
            else:
                if selector:
                    msg = f"Attempting to click element by selector: {selector}"
                    meta["narrative"].append(msg)
                    logger.info(msg)
                    await env.page.click(selector, timeout=timeout)
                else:
                    msg = f"Attempting to click button with text: {text}"
                    meta["narrative"].append(msg)
                    logger.info(msg)
                    await env.page.get_by_role("button", name=text).click(timeout=timeout)

            meta["url_after_click"] = env.page.url
            msg = f"Click successful on {meta['target']}. URL after click: {meta['url_after_click']}"
            meta["narrative"].append(msg)
            logger.info(msg)

            return ToolResponse(
                success=True,
                meta=meta
            )

        except Exception as e:
            page_content = await env.page.content()
            error_msg = f"Click failed on {meta['target']}: {str(e)}"
            meta["narrative"].append(error_msg)
            meta["narrative"].append(f"Page content:\n{page_content}")
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                error=error_msg,
                meta=meta
            )

    def description(self):
        return """Playwright tool. Click element by selector or text.
    Parameters:
    selector: str | None - CSS selector of the element to click
    text: str | None - text of the element to click

    Can use either selector or text, but not both.
    """


class FillTool(BrowserTool):
    """Atomic tool for filling input fields"""

    async def execute(
        self,
        env: BrowserEnvironment,
        selector: str,
        value: str,
        timeout: int = TIMEOUT
    ) -> ToolResponse:
        """Fill input field with value

        Parameters
        ----------
        env : BrowserEnvironment
        selector : str
            CSS selector of input field
        value : str
            Value to enter into field
        timeout : int, optional
            Maximum wait time in ms
        """
        meta = {
            "action": "fill",
            "selector": selector,
            "value": value,
            "url": env.page.url,
            "narrative": []
        }

        try:
            msg = f"Attempting to fill '{value}' into input {selector}"
            meta["narrative"].append(msg)
            logger.info(msg)

            await env.page.fill(selector, value, timeout=timeout)

            msg = f"Successfully filled '{value}' into {selector}"
            meta["narrative"].append(msg)
            logger.info(msg)

            return ToolResponse(
                success=True,
                meta=meta
            )

        except Exception as e:
            page_content = await env.page.content()
            error_msg = f"Fill failed for {selector}: {str(e)}"
            meta["narrative"].append(error_msg)
            meta["narrative"].append(f"Page content:\n{page_content}")
            logger.error(error_msg)

            return ToolResponse(
                success=False,
                error=error_msg,
                meta=meta
            )

    def description(self):
        return """Playwright tool. Fill input field with value.
    Parameters:
    selector: str - CSS selector of the input field
    value: str - Value to enter into the field
    env=browser_env, environment to act it, already initialized in scope, leave as is if using a tool
    """


class CheckContentTool(BrowserTool):
    """Tool for checking if text exists in page content"""

    async def execute(
        self,
        env: BrowserEnvironment,
        texts: list[str],
        timeout: int = TIMEOUT
    ) -> ToolResponse:
        """Check if texts are present in page content

        Parameters
        ----------
        env : BrowserEnvironment
        texts : List[str]
            List of text strings to find
        timeout : int, optional
            Maximum wait time in ms
        """
        meta = {
            "action": "check_content",
            "url": env.page.url,
            "texts": texts,
            "narrative": []
        }

        try:
            content = await env.page.content()
            found_texts = []
            missing_texts = []

            for text in texts:
                if text in content:
                    found_texts.append(text)
                else:
                    missing_texts.append(text)

            meta["found_texts"] = found_texts
            meta["missing_texts"] = missing_texts

            msg = f"Found texts: {found_texts}"
            meta["narrative"].append(msg)
            logger.info(msg)

            if missing_texts:
                msg = f"Missing texts: {missing_texts}"
                meta["narrative"].append(msg)
                logger.info(msg)

            return ToolResponse(
                success=len(missing_texts) == 0,
                error=f"Missing expected texts: {missing_texts}" if missing_texts else None,
                meta=meta
            )

        except Exception as e:
            error_msg = f"Content check failed: {str(e)}"
            meta["narrative"].append(error_msg)
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                error=error_msg,
                meta=meta
            )

    def description(self):
        return """Playwright tool. Check if texts exist in page content.
        Parameters:
        texts: List[str] - List of text strings to look for in the page content
        """


class NavigateTool(BrowserTool):
    """Tool for navigating to a URL"""

    async def execute(
        self,
        env: BrowserEnvironment,
        url: str,
        timeout: int = TIMEOUT
    ) -> ToolResponse:
        """Navigate to URL

        Parameters
        ----------
        env : BrowserEnvironment
        url : str
            URL to navigate to
        timeout : int, optional
            Maximum wait time in ms
        """
        meta = {
            "action": "navigate",
            "url": url,
            "narrative": []
        }

        try:
            msg = f"Attempting to navigate to {url}"
            meta["narrative"].append(msg)
            logger.info(msg)

            await env.page.goto(url, timeout=timeout)

            msg = f"Navigation successful to {url}"
            meta["narrative"].append(msg)
            logger.info(msg)

            return ToolResponse(
                success=True,
                meta=meta
            )

        except Exception as e:
            error_msg = f"Navigation failed to {url}: {str(e)}"
            meta["narrative"].append(error_msg)
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                error=error_msg,
                meta=meta
            )

    def description(self):
        return """Playwright tool. Navigate to URL.
        Parameters:
        url: str - URL to navigate to
        """
