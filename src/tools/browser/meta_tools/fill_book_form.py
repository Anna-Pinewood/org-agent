"""Meta tools are not atomic – they can include multiple params and tools. They can be used as tools, but they are complex."""
import logging
import re
from typing import Optional
from datetime import time

from src.tools.base import EnvTool, Tool, ToolResponse
from src.tools.browser.click import ClickTool, CheckContentTool
from src.tools.browser.click import FillTool
from src.tools.browser.environment import BrowserEnvironment
from src.config import CONFIG
logger = logging.getLogger(__name__)

default_booking_params = CONFIG.default_booking_params


class MetaFillBookingFormTool(EnvTool):
    """
    High-level tool that handles filling and submitting the room booking form.
    Assumes the form is already opened and validated by MetaBookingFormTool.
    """

    async def _verify_form_loaded(self, env: BrowserEnvironment) -> Optional[str]:
        """
        Verify booking form is properly loaded with all required fields.

        Args:
            env: Browser environment instance

        Returns:
            Optional[str]: Error message if verification fails, None if successful
        """
        expected_elements = [
            "P4_REQUEST_NAME",  # Event name field
            "P4_DATE_START",    # Start time field
            "P4_DATE_END",      # End time field
            "P4_PHONE",         # Contact phone field
            "P4_PARTICIPANTS"   # Number of participants field
        ]

        for element_id in expected_elements:
            element = await env.page.query_selector(f"#{element_id}")
            if not element:
                msg = f"Form element {element_id} not found"
                logger.error(msg)
                return msg

        logger.info("All required form elements found")
        return None

    async def _fill_event_name(
        self,
        env: BrowserEnvironment,
        event_name: str
    ) -> Optional[str]:
        """Fill event name field."""
        # TODO fix it
        event_name = default_booking_params.event_name
        result = await FillTool().execute(
            env=env,
            selector="#P4_REQUEST_NAME",
            value=event_name
        )
        if not result.success:
            logger.error("Failed to fill event name: %s", result.error)
            return result.error
        return None

    async def _fill_times(
        self,
        env: BrowserEnvironment,
        start_time: str,
        end_time: str
    ) -> Optional[str]:
        """Fill start and end time fields with time strings."""
        # Fill start time
        start_result = await FillTool().execute(
            env=env,
            selector="#P4_DATE_START",
            value=start_time
        )
        if not start_result.success:
            logger.error("Failed to fill start time: %s", start_result.error)
            return start_result.error

        # Fill end time
        end_result = await FillTool().execute(
            env=env,
            selector="#P4_DATE_END",
            value=end_time
        )
        if not end_result.success:
            logger.error("Failed to fill end time: %s", end_result.error)
            return end_result.error

        return None

    async def _fill_phone(
        self,
        env: BrowserEnvironment,
        phone: str
    ) -> Optional[str]:
        """Fill contact phone field."""
        pattern = r"^[\d\+\-\(\)\s]+$"
        if not bool(re.match(pattern, phone)):
            phone = default_booking_params.phone

        result = await FillTool().execute(
            env=env,
            selector="#P4_PHONE",
            value=phone
        )
        if not result.success:
            logger.error("Failed to fill phone number: %s", result.error)
            return result.error
        return None

    async def _fill_participants(
        self,
        env: BrowserEnvironment,
        participants: int
    ) -> Optional[str]:
        """Fill number of participants field."""
        # Validate participants count
        if not 1 <= participants <= 10000:
            msg = f"Invalid participants count {participants}. Must be between 1 and 10000"
            logger.error(msg)
            return msg

        result = await FillTool().execute(
            env=env,
            selector="#P4_PARTICIPANTS",
            value=str(participants)
        )
        if not result.success:
            logger.error("Failed to fill participants count: %s", result.error)
            return result.error
        return None

    async def _submit_form(
        self,
        env: BrowserEnvironment,
        save_as_draft: bool
    ) -> Optional[str]:
        """Submit form or save as draft."""
        try:
            button_id = "createProjectButton" if save_as_draft else "ButtonPassRequest"
            button_text = "Сохранить как проект" if save_as_draft else "Подать заявку"

            # # Click appropriate button
            # click_result = await ClickTool().execute(
            #     env=env,
            #     selector=f"#{button_id}",
            #     wait_for_navigation=False,
            #     # timeout=30000
            # )
            button = await env.page.query_selector(f"#{button_id}")
            await button.click()

            # Verify submission
            try:
                # Wait for text to appear
                expected_text = "Проект успешно создан." if save_as_draft else "Заявка отправлена"
                await env.page.wait_for_function(
                    f'document.body.textContent.includes("{expected_text}")',
                    timeout=5000
                )

                logger.info("Form %s successfully",
                            "saved as draft" if save_as_draft else "submitted")
                return None

            except Exception as e:
                msg = f"Form submission verification failed: {expected_text} not found"
                logger.error(msg)
                return msg

        except Exception as e:
            msg = f"Form submission failed: %s", str(e)
            logger.error(msg)
            return msg

    def _parse_time(self, time_str: str | time) -> str:
        """
        Parse object time into string

        Returns:
            Time string in HH:MM format or time object
        """
        if isinstance(time_str, str):
            return time_str
        try:
            return time_str.strftime("%H:%M")
        except ValueError as e:
            logger.error("Failed to parse time string '%s': %s",
                         time_str, str(e))
            raise ValueError(
                f"Invalid time format. Expected HH:MM, got: {time_str}")

    async def execute(
        self,
        env: BrowserEnvironment,
        event_name: str = default_booking_params.event_name,
        start_time: time | str = default_booking_params.start_time,
        end_time: time | str = default_booking_params.end_time,
        phone: str = default_booking_params.phone,
        participants: int = 15,
        save_as_draft: bool = False
    ) -> ToolResponse:
        save_as_draft = True
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
            start_time = self._parse_time(start_time)
            end_time = self._parse_time(end_time)
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
