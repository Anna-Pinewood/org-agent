"""Meta tools are not atomic – they can include multiple params and tools. They can be used as tools, but they are complex."""
import logging
from datetime import time, datetime
from typing import List, Optional, Tuple

from config import CONFIG
from src.tools.base import EnvTool, Tool, ToolResponse
from src.tools.browser.click import ClickTool, CheckContentTool, NavigateTool
from src.tools.browser.dropdown import DropdownOptionsTool, DropDownTool
from src.tools.browser.environment import BrowserEnvironment
from src.tools.browser.booking_utils import (
    GetAvailableRoomsTool,
    GetTimeIntervalsTool,
    GetRoomIdTool,
    CheckRoomAvailableTool,
    UNIVERSITY_INTERVALS
)
from src.tools.browser.get_text import GetTextTool

logger = logging.getLogger(__name__)

MONTH_MAP = {
    'Январь': 0, 'Февраль': 1, 'Март': 2, 'Апрель': 3,
    'Май': 4, 'Июнь': 5, 'Июль': 6, 'Август': 7,
    'Сентябрь': 8, 'Октябрь': 9, 'Ноябрь': 10, 'Декабрь': 11
}


class MetaBookingFormTool(EnvTool):
    """
    High-level tool that combines multiple atomic tools to handle the complete room booking process for a single room. 

    This tool expects to start on any page and will navigate to the booking page.
    """

    async def _select_building(self, env: BrowserEnvironment, building: str) -> Optional[str]:
        """
        Select building from dropdown

        Args:
            env: Browser environment
            building: Building name to select

        Returns:
            Error message if failed, None if successful
        """
        # Get available building options
        options_result = await DropdownOptionsTool().execute(
            env=env,
            dropdown_selector='.select2-chosen'
        )
        if not options_result.success:
            msg = "Failed to get building options: %s"
            logger.error(msg, options_result.error)
            return msg % options_result.error

        # Verify building exists in options
        if building not in options_result.meta['options']:
            msg = "Building '%s' not found in available options: %s"
            logger.error(msg, building, options_result.meta['options'])
            return msg % (building, options_result.meta['options'])

        # Select building
        select_result = await DropDownTool().execute(
            env=env,
            option_text=building,
            dropdown_selector='.select2-chosen'
        )
        if not select_result.success:
            msg = "Failed to select building: %s"
            logger.error(msg, select_result.error)
            return msg % select_result.error

        # Verify selection
        verify_result = await CheckContentTool().execute(
            env=env,
            texts=[building]
        )
        if not verify_result.success:
            return "Building selection could not be verified"

        return None

    async def _navigate_to_booking_page(self, env: BrowserEnvironment) -> Optional[str]:
        """Navigate to booking page and verify"""
        nav_result = await NavigateTool().execute(
            env=env,
            url=CONFIG.isu_booking_creds.creating_application_url
        )
        if not nav_result.success:
            msg = "Failed to navigate to booking page: %s"
            logger.error(msg, nav_result.error)
            return msg % nav_result.error

        check_result = await CheckContentTool().execute(
            env=env,
            texts=["Бронирование помещений"]
        )
        if not check_result.success:
            return "Not on booking page - expected text not found"

        return None

    async def _get_current_month_year(
        self,
        env: BrowserEnvironment
    ) -> Tuple[Optional[str], Optional[str]]:
        """Get current month and year from calendar"""
        month_result = await GetTextTool().execute(
            env=env,
            selector=".ui-datepicker-month"
        )
        year_result = await GetTextTool().execute(
            env=env,
            selector=".ui-datepicker-year"
        )

        if not month_result.success or not year_result.success:
            logger.error("Failed to get current month/year")
            return None, None

        return (month_result.meta['result'], year_result.meta['result'])

    async def _select_date(self, env: BrowserEnvironment, date: str) -> Optional[str]:
        """Select date in calendar"""
        # Format date string
        target_date = datetime.strptime(date, "%d-%m-%Y")
        target_date_dots = target_date.strftime("%d.%m.%Y")

        # Open calendar
        click_result = await ClickTool().execute(
            env=env,
            selector="#P4_DATE",
            wait_for_navigation=False
        )
        if not click_result.success:
            msg = "Failed to open calendar: %s"
            logger.error(msg, click_result.error)
            return msg % click_result.error

        # Verify calendar opened
        calendar_check = await CheckContentTool().execute(
            env=env,
            texts=["ui-datepicker-calendar",
                   "ui-datepicker-month", "ui-datepicker-year"]
        )
        if not calendar_check.success:
            return "Calendar did not open properly"

        # Get current month/year
        current_month_text, current_year_text = await self._get_current_month_year(env)
        if not current_month_text or not current_year_text:
            return "Failed to get current month/year"

        # Calculate months difference
        current_month_num = MONTH_MAP[current_month_text]
        current_year_num = int(current_year_text)
        target_month_idx = target_date.month - 1
        months_diff = (target_date.year - current_year_num) * \
            12 + (target_month_idx - current_month_num)

        # Navigate to target month
        if months_diff > 0:
            for _ in range(months_diff):
                await ClickTool().execute(
                    env=env,
                    selector=".ui-datepicker-next",
                    wait_for_navigation=False
                )

        # Select target date
        date_selector = (
            f'[data-handler="selectDay"]'
            f'[data-month="{target_date.month - 1}"]'
            f'[data-year="{target_date.year}"]'
            f' a:text("{target_date.day}")'
        )
        date_click = await ClickTool().execute(
            env=env,
            selector=date_selector,
            wait_for_navigation=False
        )
        if not date_click.success:
            msg = "Failed to click date: %s"
            logger.error(msg, date_click.error)
            return msg % date_click.error

        # Verify date selected
        input_value = await env.page.input_value("#P4_DATE")
        if not input_value or input_value != target_date_dots:
            return "Date was not properly selected"

        return None

    async def _verify_room_available(
        self,
        env: BrowserEnvironment,
        room_number: str,
        available_rooms: List[str]
    ) -> Optional[str]:
        """Verify if room is available"""
        if room_number not in available_rooms:
            msg = "Room %s is not in available rooms list"
            logger.error(msg, room_number)
            return msg % room_number
        return None

    async def _verify_time_slots(
        self,
        env: BrowserEnvironment,
        room_id: str,
        room_number: str,
        time_intervals: List[str]
    ) -> Optional[str]:
        """Verify time slot availability"""
        availability = await CheckRoomAvailableTool().execute(
            env=env,
            room_id=room_id,
            time_intervals=time_intervals,
            room_number=room_number
        )

        if not availability.success:
            msg = "Failed to check room availability: %s"
            logger.error(msg, availability.error)
            return msg % availability.error

        if not all(availability.meta['result']):
            unavailable = [
                interval for interval, is_available
                in zip(time_intervals, availability.meta['result'])
                if not is_available
            ]

            unavailable_periods = []
            for interval in unavailable:
                interval_times = UNIVERSITY_INTERVALS.get(interval, {})
                if interval_times:
                    start = interval_times['start'].strftime('%H:%M')
                    end = interval_times['end'].strftime('%H:%M')
                    unavailable_periods.append(f"{start}-{end}")

            msg = "Room %s is not available for the periods: %s, which interferes with the requested booking time. Consider changing a room or time slots."
            formatted_periods = ", ".join(unavailable_periods)
            logger.error(msg, room_number, formatted_periods)
            return msg % (room_number, formatted_periods)

        return None

    async def _open_schedule_and_select_room(
        self,
        env: BrowserEnvironment,
        room_id: str,
        time_intervals: List[str]
    ) -> bool:
        """Open schedule and select room"""
        cell = f'td.reserve[roomid="{room_id}"][interval="{time_intervals[0]}"]'
        click_result = await ClickTool().execute(
            env=env,
            selector=cell,
            wait_for_navigation=False
        )
        if not click_result.success:
            logger.error(
                "Failed to click room cell: %s",
                click_result.error
            )
            return False

        return True

    async def _verify_booking_form(self, env: BrowserEnvironment) -> bool:
        """Verify booking form displayed"""
        expected_texts = [
            "Требуется техническое сопровождение мероприятия",
            "Контактный телефон",
            "Название мероприятия"
        ]

        check_result = await CheckContentTool().execute(
            env=env,
            texts=expected_texts
        )
        if not check_result.success:
            logger.error(
                "Booking form verification failed: %s",
                check_result.error
            )
            return False

        return True

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
        room_number: str,
        start_time: str | time,
        end_time: str | time,
        building: str,
        date: str  # Format: DD-MM-YYYY
    ) -> ToolResponse:
        """
        Execute complete room booking process

        Args:
            env: Browser environment
            room_number: Room number to book
            start_time: Booking start time
            end_time: Booking end time
            building: Building name
            date: Booking date in DD-MM-YYYY format

        Returns:
            ToolResponse: 
                success: True if booking form prepared successfully
                error: Error message if any step failed
                meta: Contains room_id, time_intervals if successful
        """
        try:
            # Convert tome objects to time strings
            start_time_obj = self._parse_time(start_time)
            end_time_obj = self._parse_time(end_time)

            logger.info("%s Navigating to booking page... %s", "*"*10, "*"*10)
            # Step 1: Navigate and verify page
            if error := await self._navigate_to_booking_page(env):
                return ToolResponse(success=False, error=error)

            logger.info("%s Selecting building... %s", "*"*10, "*"*10)
            # Step 2: Select building
            if error := await self._select_building(env, building):
                return ToolResponse(success=False, error=error)

            logger.info('%s Selecting date "%s" %s', "*"*10, date, "*"*10)
            # Step 3: Select date
            if error := await self._select_date(env, date):
                return ToolResponse(success=False, error=error)

            logger.info("%s Opening schedule table... %s", "*"*10, "*"*10)
            # Step 4: Opening schedule table
            click_result = await ClickTool().execute(
                env=env,
                selector="#P4_AUD_NAME",
                wait_for_navigation=False
            )
            if not click_result.success:
                error = f"Failed to click room input: {click_result.error}"
                logger.error(error)
                return ToolResponse(success=False, error=click_result.error)

            logger.info("%s Getting available rooms... %s", "*"*10, "*"*10)
            # Step 5: Get available rooms
            available_rooms_result = await GetAvailableRoomsTool().execute(env=env)
            if not available_rooms_result.success:
                return ToolResponse(
                    success=False,
                    error=f"Failed to get available rooms: {available_rooms_result.error}"
                )

            logger.info("%s Verifying room availability... %s", "*"*10, "*"*10)
            # Step 6: Verify room available
            if error := await self._verify_room_available(
                env=env,
                room_number=room_number,
                available_rooms=available_rooms_result.meta['result']
            ):
                return ToolResponse(success=False, error=error)

            logger.info("%s Getting time intervals... %s", "*"*10, "*"*10)
            # Step 7: Get time intervals
            intervals_result = GetTimeIntervalsTool().execute(
                start_time=start_time_obj,
                end_time=end_time_obj
            )
            if not intervals_result.success:
                return ToolResponse(
                    success=False,
                    error=f"Failed to get time intervals: {intervals_result.error}"
                )

            logger.info("%s Getting room ID... %s", "*"*10, "*"*10)
            # Step 8: Get room ID
            room_id_result = await GetRoomIdTool().execute(
                env=env,
                room_number=room_number
            )
            if not room_id_result.success:
                return ToolResponse(
                    success=False,
                    error=f"Failed to get room ID: {room_id_result.error}"
                )

            logger.info("%s Verifying time slots... %s", "*"*10, "*"*10)
            # Step 9: Verify time slots
            if error := await self._verify_time_slots(
                env=env,
                room_id=room_id_result.meta['result'],
                room_number=room_number,
                time_intervals=intervals_result.meta['result']
            ):
                return ToolResponse(success=False, error=error)

            logger.info(
                "%s Opening schedule and selecting room... %s", "*"*10, "*"*10)
            # Step 10: Open schedule and select room
            if not await self._open_schedule_and_select_room(
                env=env,
                room_id=room_id_result.meta['result'],
                time_intervals=intervals_result.meta['result']
            ):
                return ToolResponse(
                    success=False,
                    error="Failed to open schedule and select room"
                )

            logger.info("%s Verifying booking form... %s", "*"*10, "*"*10)
            # Step 11: Verify booking form
            if not await self._verify_booking_form(env):
                return ToolResponse(
                    success=False,
                    error="Booking form verification failed"
                )

            logger.info("%s Booking form prepared successfully %s",
                        "*"*10, "*"*10)
            return ToolResponse(
                success=True,
                meta={
                    "room_number": room_number,
                    "room_id": room_id_result.meta['result'],
                    "time_intervals": intervals_result.meta['result'],
                    "message": f"Successfully prepared booking form for room {room_number}"
                }
            )

        except Exception as e:
            logger.error(
                "Unexpected error in MetaBookingTool: %s",
                str(e),
                exc_info=True
            )
            return ToolResponse(
                success=False,
                error=f"Unexpected error: {str(e)}"
            )

    def description(self) -> str:
        return """Handle opening a booking form for selected room, verifying it's available in the selected time slots.

Args:
    room_number: Room number to book (e.g. "1229")
    start_time: Booking string start time (e.g. "18:40")
    end_time: Booking string end time
    building: Building name
    date: Booking string date in DD-MM-YYYY format
"""
