import logging
from datetime import datetime, time
from typing import List, Dict

from src.config import CONFIG
from src.scenarios.base import ScenarioStep, StepStatus
from src.tools.browser.click import CheckContentTool
from src.tools.browser.meta_tools.book_room_form import MetaBookingFormTool
from src.tools.browser.meta_tools.fill_book_form import MetaFillBookingFormTool
from src.tools.browser.environment import BrowserEnvironment
from src.tools.call_human import CallHumanTool

logger = logging.getLogger(__name__)


class RoomBookingStep(ScenarioStep):
    """Single room booking sequence"""

    def __init__(self, room_number: str, meta: dict):
        super().__init__()
        self.room_number = room_number
        self.meta = meta
        self._register_tools()

    def _register_tools(self):
        self.toolbox.register_tool(
            "MetaBookingFormTool", MetaBookingFormTool())
        self.toolbox.register_tool(
            "MetaFillBookingFormTool", MetaFillBookingFormTool())
        self.toolbox.register_tool("CallHumanTool", CallHumanTool())
        self.toolbox.register_tool("CheckContentTool", CheckContentTool())

    async def execute(self, env) -> bool:
        """Execute room booking sequence"""
        logger.info("Booking room %s", self.room_number)

        # Step 1: Open form
        form_result = await MetaBookingFormTool().execute(
            env=env,
            room_number=self.room_number,
            start_time=self.meta['start_time'],
            end_time=self.meta['end_time'],
            building=self.meta['building'],
            date=self.meta['date'].strftime("%d-%m-%Y")
        )
        await self._record_tool_execution(
            tool_name="MetaBookingFormTool",
            params={
                "room_number": self.room_number,
                "start_time": self.meta['start_time'],
                "end_time": self.meta['end_time'],
                "building": self.meta['building'],
                "date": self.meta['date'].strftime("%d-%m-%Y")
            },
            response=form_result,
            environment=env,
            header_summary=f"Opening booking form for room {self.room_number}"
        )

        if not form_result.success:
            return False

        # Step 2: Fill and submit
        fill_result = await MetaFillBookingFormTool().execute(
            env=env,
            event_name=self.meta['event_name'],
            start_time=self.meta['start_time'],
            end_time=self.meta['end_time'],
            save_as_draft=True
        )
        await self._record_tool_execution(
            tool_name="MetaFillBookingFormTool",
            params={
                "event_name": f"Room {self.room_number} Booking",
                "start_time": self.meta['start_time'],
                "end_time": self.meta['end_time'],
                "save_as_draft": True
            },
            response=fill_result,
            environment=env,
            header_summary=f"Filling and submitting booking form for room {self.room_number}"
        )
        return fill_result.success

    async def verify_success(self, environment=None) -> bool:
        # TODO: Implement verification of successful booking
        # Verify submission
        try:
            # TODO: Implement real page checking
            # Wait for text to appear
            expected_text = "Проект успешно создан."
            await environment.page.wait_for_function(
                f'document.body.textContent.includes("{expected_text}")',
                timeout=5000
            )
            return True

        except Exception as e:
            msg = f"Application submission verification failed: {expected_text} not found"
            logger.error(msg)
            return False
