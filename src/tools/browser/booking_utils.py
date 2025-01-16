from datetime import datetime, time
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from src.tools.base import Tool, ToolResponse
from src.tools.browser.base import BrowserTool
from src.tools.browser.click import TIMEOUT, ClickTool
from src.tools.browser.environment import BrowserEnvironment

logger = logging.getLogger(__name__)

# Define university time intervals as constants
UNIVERSITY_INTERVALS = {
    "1": {"start": time(8, 20), "end": time(9, 50)},
    "2": {"start": time(10, 0), "end": time(11, 30)},
    "3": {"start": time(11, 40), "end": time(13, 10)},
    "4": {"start": time(13, 30), "end": time(15, 0)},
    "5": {"start": time(15, 20), "end": time(16, 50)},
    "6": {"start": time(17, 0), "end": time(18, 30)},
    "7": {"start": time(18, 40), "end": time(20, 10)},
    "8": {"start": time(20, 20), "end": time(21, 50)},
    "9": {"start": time(22, 0), "end": time(23, 00)},
}


class GetTimeIntervalsTool(Tool):
    """Tool for mapping start and end times to university time interval numbers."""

    def execute(self,
                start_time: time | str,
                end_time: time | str) -> ToolResponse:
        """
        Find all university intervals that overlap with the given timespan.
        An interval is included if there is any overlap with the timespan.

        Args:
            start_time: Start time to check
            end_time: End time to check

        Returns:
            ToolResponse with matching intervals in meta['result']
        """
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, "%H:%M").time()
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, "%H:%M").time()
        try:
            matching_intervals = []

            def time_to_minutes(t: time) -> int:
                return t.hour * 60 + t.minute

            span_start = time_to_minutes(start_time)
            span_end = time_to_minutes(end_time)

            for interval_num, interval in UNIVERSITY_INTERVALS.items():
                interval_start = time_to_minutes(interval["start"])
                interval_end = time_to_minutes(interval["end"])

                # Check if there's any overlap
                if span_start < interval_end and span_end > interval_start:
                    matching_intervals.append(interval_num)
                    logger.info(
                        "Time %s-%s overlaps with interval %s (%s-%s)",
                        start_time, end_time,
                        interval_num,
                        interval["start"], interval["end"]
                    )

            if not matching_intervals:
                logger.warning(
                    "No matching intervals found for timespan %s-%s",
                    start_time, end_time
                )

            return ToolResponse(
                success=True,
                meta={
                    "result": matching_intervals,
                    "timespan": f"{start_time}-{end_time}"
                }
            )

        except Exception as e:
            error_msg = f"Error finding matching intervals: {str(e)}"
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                error=error_msg
            )

    def description(self) -> str:
        return "Map start and end times to university time intervals"


class GetRoomIdTool(BrowserTool):
    """Tool for extracting room_id from page content."""

    async def execute(self,
                      env: BrowserEnvironment,
                      room_number: str) -> ToolResponse:
        """
        Extract room_id from page content for a given room number.

        Args:
            env: Browser environment
            room_number: Room number to find ID for

        Returns:
            ToolResponse with room_id in meta['result'] if found
        """
        try:
            page_content = await env.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            schedule_table = soup.find('table', class_='scheduleTable')

            if not schedule_table:
                error_msg = "Schedule table not found in page content"
                logger.error(error_msg)
                return ToolResponse(success=False, error=error_msg)

            header_row = schedule_table.find('thead').find_all('tr')[1]
            room_cells = header_row.find_all('th', class_='event_room')

            target_index = None
            for idx, cell in enumerate(room_cells):
                if cell.text.strip() == room_number:
                    target_index = idx
                    break

            if target_index is None:
                error_msg = f"Room number {room_number} not found in table headers"
                logger.warning(error_msg)
                return ToolResponse(success=False, error=error_msg)

            first_data_row = schedule_table.find('tbody').find('tr')
            cells = first_data_row.find_all('td')
            target_cell = cells[target_index + 2]
            room_id = target_cell.get('roomid')

            if not room_id:
                error_msg = f"Could not find room_id attribute in cell for room {room_number}"
                logger.warning(error_msg)
                return ToolResponse(success=False, error=error_msg)

            logger.info("Found room_id %s for room number %s",
                        room_id, room_number)
            return ToolResponse(
                success=True,
                meta={
                    "result": room_id,
                    "room_number": room_number
                }
            )

        except Exception as e:
            error_msg = f"Error extracting room_id for room {room_number}: {str(e)}"
            logger.error(error_msg)
            return ToolResponse(success=False, error=error_msg)

    def description(self) -> str:
        return "Extract room_id from page content for a given room number"


class GetAvailableRoomsTool(BrowserTool):
    """Tool for getting list of available rooms from schedule table."""

    async def execute(self, env: BrowserEnvironment) -> ToolResponse:
        """
        Get list of rooms that have available slots.

        Args:
            env: Browser environment instance

        Returns:
            ToolResponse with list of available room numbers in meta['result']
        """
        try:
            page_content = await env.page.content()
            soup = BeautifulSoup(page_content, 'html.parser')
            schedule_table = soup.find('table', class_='scheduleTable')

            if not schedule_table:
                error_msg = "Schedule table not found in page content"
                logger.error(error_msg)
                return ToolResponse(success=False, error=error_msg)

            header_row = schedule_table.find('thead').find_all('tr')[1]
            room_cells = header_row.find_all('th', class_='event_room')
            rooms = [cell.text.strip() for cell in room_cells]

            available_rooms = []
            tbody = schedule_table.find('tbody')

            for room_idx, room in enumerate(rooms):
                room_cells = [row.find_all('td')[room_idx + 2]
                              for row in tbody.find_all('tr')]

                if any('reserve' in cell.get('class', [])
                       for cell in room_cells):
                    available_rooms.append(room)
                    logger.debug("Room %s has available slots", room)

            logger.info("Found %d available rooms", len(available_rooms))
            return ToolResponse(
                success=True,
                meta={
                    "result": available_rooms,
                    "total_found": len(available_rooms)
                }
            )

        except Exception as e:
            error_msg = f"Error getting available rooms: {str(e)}"
            logger.error(error_msg)
            return ToolResponse(success=False, error=error_msg)

    def description(self) -> str:
        return "Get list of room numbers that have at least one available timeslot"


class CheckRoomAvailableTool(Tool):
    """Tool for checking if room is available during specified intervals."""

    async def execute(
        self,
        env: BrowserEnvironment,
        room_id: str,
        time_intervals: list[str],
        room_number: str | None = None  # For logging purposes
    ) -> ToolResponse:
        """
        Check room availability for given intervals.

        Args:
            env: Browser environment
            room_id: Room ID to check
            time_intervals: List of interval numbers (1-9)
            room_number: Optional room number for logging

        Returns:
            ToolResponse with availability list in meta['result']
        """
        try:
            results = []
            for interval in time_intervals:
                if interval == "9":
                    logger.warning(
                        "Interval 9 is 22-23 and considered always available"
                    )
                    results.append(True)
                    continue

                # Check for available cell
                free_selector = f'td.reserve[roomid="{room_id}"][interval="{interval}"]'
                free_cell = await env.page.query_selector(free_selector)

                if free_cell:
                    logger.info(
                        "Room %s (ID=%s) is available at interval %s",
                        room_number or room_id, room_id, interval
                    )
                    results.append(True)
                    continue

                # Check if room exists but is booked
                busy_selector = f'td.busy[roomid="{room_id}"]'
                busy_cell = await env.page.query_selector(busy_selector)

                if busy_cell:
                    logger.info(
                        "Room %s (ID=%s) is booked at interval %s",
                        room_number or room_id, room_id, interval
                    )
                    results.append(False)
                else:
                    logger.error(
                        "No cell found for room %s (ID=%s) at interval %s - room may not exist",
                        room_number or room_id, room_id, interval
                    )
                    results.append(False)

            return ToolResponse(
                success=True,
                meta={
                    "result": results,
                    "room_id": room_id,
                    "room_number": room_number,
                    "intervals_checked": time_intervals
                }
            )

        except Exception as e:
            error_msg = f"Error checking availability for room {room_number or room_id}: {str(e)}"
            logger.error(error_msg)
            return ToolResponse(
                success=False,
                error=error_msg,
                meta={
                    "room_id": room_id,
                    "room_number": room_number,
                    "intervals_checked": time_intervals
                }
            )

    def description(self) -> str:
        return "Check if room is available during specified time intervals"
