import logging
from typing import Optional
from src.config import CONFIG
from src.tools.base import ToolResponse
from src.tools.browser.base import BrowserTool
from src.tools.browser.environment import BrowserEnvironment

logger = logging.getLogger(__name__)

TIMEOUT = CONFIG.isu_booking_creds.page_interaction_timeout


class GetTextTool(BrowserTool):
    """Tool for getting text content of elements by selector or role"""

    async def execute(
        self,
        env: BrowserEnvironment,
        selector: str | None = None,
        role: str | None = None,
        name: str | None = None,
        include_hidden: bool = False,
        timeout: int = TIMEOUT
    ) -> ToolResponse:
        """Get text content of element

        Parameters
        ----------
        env : BrowserEnvironment 
        selector : str | None
            CSS selector of element
        role : str | None
            ARIA role of element (e.g. "button", "heading")
        name : str | None
            Accessible name of element with given role
        include_hidden : bool
            Whether to include hidden elements
        timeout : int
            Maximum wait time in ms
        """
        meta = {
            "action": "get_text",
            "selector": selector,
            "role": role,
            "name": name,
            "url": env.page.url,
            "narrative": []
        }

        try:
            element = None
            if selector:
                msg = f"Getting text by selector: {selector}"
                meta["narrative"].append(msg)
                logger.info(msg)
                element = await env.page.wait_for_selector(
                    selector,
                    timeout=timeout,
                    state="attached"
                )
            elif role:
                msg = f"Getting text by role: {role}"
                if name:
                    msg += f" and name: {name}"
                meta["narrative"].append(msg)
                logger.info(msg)
                element = await env.page.get_by_role(
                    role,
                    name=name if name else None
                ).element_handle()

            if not element:
                msg = f"Element not found"
                meta["narrative"].append(msg)
                logger.error(msg)
                return ToolResponse(success=False, error=msg, meta=meta)

            text = await element.text_content()
            if not include_hidden and not await element.is_visible():
                msg = "Element is hidden"
                meta["narrative"].append(msg)
                logger.warning(msg)
                return ToolResponse(success=False, error=msg, meta=meta)

            meta["result"] = text.strip()
            msg = f"Found text: {text}"
            meta["narrative"].append(msg)
            logger.info("Got text content: %s", text)

            return ToolResponse(success=True, meta=meta)

        except Exception as e:
            error_msg = f"Failed to get text: {str(e)}"
            meta["narrative"].append(error_msg)
            logger.error(error_msg)
            return ToolResponse(success=False, error=error_msg, meta=meta)

    def description(self):
        return """Playwright tool. Get text content of element by CSS selector or ARIA role.
Can find elements by:
- selector: CSS selector
- role: ARIA role (button, heading etc)
- name: Accessible name for role
"""
