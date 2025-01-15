"""Meta tools are not atomic – they can include multiple params and tools. They can be used as tools, but they are complex."""
import logging
from typing import Optional
from datetime import time

from src.tools.base import Tool, ToolResponse
from src.tools.browser.click import ClickTool, CheckContentTool
from src.tools.browser.click import FillTool
from src.tools.browser.environment import BrowserEnvironment
from src.config import CONFIG

logger = logging.getLogger(__name__)


class MetaRoomNumbersTool(Tool):

    async def execute(
        self,
        env: BrowserEnvironment,
        r
    ) -> ToolResponse:
        """
        Fill and submit the booking form.

        Args:
            env: Browser environment instance
            event_name: Name/description of the event
            start_time: Booking start time
            end_time: Booking end time 
            phone: Contact phone number (defaults to config)
            participants: Expected number of participants (defaults to 10)
            save_as_draft: Whether to save as draft instead of submitting

        Returns:
            ToolResponse:
                success: True if form submitted successfully
                error: Error message if any step failed
                meta: Contains submission status information
        """
        try:
            # Step 1: Verify form is loaded
            if error := await self._verify_form_loaded(env):
                return ToolResponse(
                    success=False,
                    error=f"Form verification failed: {error}"
                )

            # Step 2: Fill event name
            if error := await self._fill_event_name(env, event_name):
                return ToolResponse(
                    success=False,
                    error=error
                )

            # Step 3: Fill times
            if error := await self._fill_times(env, start_time, end_time):
                return ToolResponse(
                    success=False,
                    error=error
                )

            # Step 4: Fill contact phone
            if error := await self._fill_phone(env, phone):
                return ToolResponse(
                    success=False,
                    error=error
                )

            # Step 5: Fill participants count
            if error := await self._fill_participants(env, participants):
                return ToolResponse(
                    success=False,
                    error=error
                )

            # Step 6: Submit form
            if error := await self._submit_form(env, save_as_draft):
                return ToolResponse(
                    success=False,
                    error=error
                )

            return ToolResponse(
                success=True,
                meta={
                    "status": "draft" if save_as_draft else "submitted",
                    "event_name": event_name,
                    "message": "Form saved as draft" if save_as_draft else "Form submitted successfully",
                }
            )

        except Exception as e:
            error_msg = f"Unexpected error in MetaFillBookingFormTool: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return ToolResponse(
                success=False,
                error=error_msg
            )

    def description(self) -> str:
        return """Fill and submit a room booking form that's already opened.

Args:
    event_name: Name/description of the event
    start_time: Booking start time (datetime.time object)
    end_time: Booking end time (datetime.time object)
    phone: Contact phone number (optional, defaults to config)
    participants: Expected number of participants (optional, defaults to 10)
    save_as_draft: Whether to save as draft instead of submitting (optional, defaults to False)
"""
