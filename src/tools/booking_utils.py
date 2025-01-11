from datetime import datetime, time
import logging
from typing import Dict, List, Optional
from bs4 import BeautifulSoup
from src.tools.base import Tool

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


class GetIntervalsForTimespanTool(Tool):
    """Tool for mapping start and end times to university time interval numbers."""

    def execute(self, start_time: time, end_time: time) -> List[str]:
        """
        Find all university intervals that overlap with the given timespan.
        An interval is included if there is any overlap with the timespan.
        """
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

        return matching_intervals

    def description(self) -> str:
        return "Map start and end times to university time intervals"


class GetRoomIdFromTableTool(Tool):
    """Tool for extracting room_id from page content."""

    def execute(self, page_content: str, room_number: str) -> Optional[str]:
        """Extract room_id from page content for a given room number"""
        try:
            soup = BeautifulSoup(page_content, 'html.parser')
            schedule_table = soup.find('table', class_='scheduleTable')
            if not schedule_table:
                logger.error("Schedule table not found in page content")
                return None

            header_row = schedule_table.find('thead').find_all('tr')[1]
            room_cells = header_row.find_all('th', class_='event_room')

            target_index = None
            for idx, cell in enumerate(room_cells):
                if cell.text.strip() == room_number:
                    target_index = idx
                    break

            if target_index is None:
                logger.warning(
                    "Room number %s not found in table headers", room_number)
                return None

            first_data_row = schedule_table.find('tbody').find('tr')
            cells = first_data_row.find_all('td')
            target_cell = cells[target_index + 2]
            room_id = target_cell.get('roomid')

            if not room_id:
                logger.warning(
                    "Could not find room_id attribute in cell for room %s",
                    room_number
                )
                return None

            logger.info("Found room_id %s for room number %s",
                        room_id, room_number)
            return room_id

        except Exception as e:
            logger.error(
                "Error extracting room_id for room %s: %s",
                room_number, str(e)
            )
            return None

    def description(self) -> str:
        return "Extract room_id from page content for a given room number"