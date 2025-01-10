from datetime import datetime, time
from pydantic import BaseModel, Field, field_validator
from scenarios.base import BaseScenario
import logging
from config import CONFIG
from tools.browser import BookingPageTool, LoginTool
from tools.date import CurrentDateTool, next_thursday
from llm_interface import LLMInterface
from pydantic.functional_validators import BeforeValidator
from typing import Annotated
logger = logging.getLogger(__name__)

default_booking_params = CONFIG.default_booking_params

DateFormatConvert = Annotated[
    datetime,
    BeforeValidator(lambda x: datetime.strptime(
        x, "%d-%m-%Y") if isinstance(x, str) else x)
]
TimeFormatConvert = Annotated[
    time,
    BeforeValidator(lambda x: datetime.strptime(
        x, "%H:%M").time() if isinstance(x, str) else x)
]


class BookingParams(BaseModel):
    room_count: int = Field(description="Number of rooms to book")
    date: DateFormatConvert = Field(
        description="Calculated booking date in DD-MM-YYYY   format",
        default=next_thursday())
    start_time: TimeFormatConvert = Field(
        description="Start time of booking in HH:MM format",
        default=datetime.strptime(
            default_booking_params.start_time, "%H:%M").time())
    end_time: TimeFormatConvert = Field(
        description="End time of booking in HH:MM format",
        default=datetime.strptime(
            default_booking_params.end_time, "%H:%M").time())
    building: str = Field(
        description="Building name if specified",
        default=default_booking_params.building)


PARSE_BOOKING_PROMPT = """Parse the booking command and extract parameters.
Current date: {current_date}
Command: {user_command}

Return a JSON with this structure:
{{
    "room_count": int,
    "date": "DD-MM-YYYY" | null, # You should calculate this based on the current date
    "start_time": "HH:MM" | null,
    "end_time": "HH:MM" | null,
    "building": string | null
}}

Return only valid JSON without comments or explanations.

Example input:
Current date: 07 January 2025, Tuesday
Command: "забронируй 3 аудитории на следующий четверг с 6 до 10 вечера на кронверкском проспекте"

Example output:
{{
    "room_count": 3,
    "date": 09-01-2025",
    "start_time": "18:00",
    "end_time": "22:00",
    "building": "Кронверкский проспект"
}}"""


class BookingScenario(BaseScenario):
    """Scenario for handling room booking requests with authentication support"""

    def __init__(self, llm_brain: LLMInterface | None = None):
        """Initialize booking scenario"""
        super().__init__(llm_brain)
        self.current_date = CurrentDateTool().execute()

    async def authenticate(self) -> bool:
        """
        Check authentication status and login if necessary

        Returns:
            bool: True if authenticated (either already or after login), False otherwise
        """
        try:
            # Check current auth status
            status = await BookingPageTool().execute()

            if status.get('status') == 'logged_in':
                logger.info("User already authenticated")
                return True

            if status.get('status') == 'login_required':
                logger.info("Login required, attempting authentication")
                login_result = await LoginTool().execute()

                if login_result.get('success'):
                    logger.info("Login successful")
                    return True

                logger.error("Login failed: %s", login_result.get('error'))
                return False

            logger.error("Unexpected auth status: %s", status.get('status'))
            return False

        except Exception as e:
            logger.error("Authentication process failed: %s", str(e))
            return False

    def classify_intent(self, command: str) -> float:
        """
        Check if command contains booking-related words (with root 'брон')

        Args:
            command: User's natural language command

        Returns:
            float: 1.0 if booking-related, 0.0 otherwise
        """
        command = command.lower()
        booking_stems = ['брон']

        for stem in booking_stems:
            if stem in command:
                logger.info("Booking intent detected with stem '%s'", stem)
                return 1.0

        logger.debug("No booking intent detected")
        return 0.0

    def parse_command(self, command: str, **kwargs) -> BookingParams:
        """
        Parse natural language booking command into structured parameters

        Args:
            command: User's natural language command
            **kwargs: Additional parameters for LLM interface

        Returns:
            BookingParams: Structured booking parameters
        """
        response = self.llm_brain.send_request(
            prompt=PARSE_BOOKING_PROMPT,
            call_params={"user_command": command,
                         "current_date": self.current_date["readable"]},
            response_format={"type": "json_object"},
            **kwargs
        )
        parsed = self.llm_brain.get_response_content(response)
        logger.info("Booking command parsed: %s", parsed)
        result_clean = {key: value for key,
                        value in parsed.items() if value is not None}

        return BookingParams(**result_clean)

    async def execute(self, command: str) -> None:
        """
        Execute the booking scenario with authentication

        Args:
            command: User's natural language command

        Raises:
            NotImplementedError: When booking execution is not yet implemented
        """
        self._log_execution(command)

        # Authenticate first
        if not await self.authenticate():
            logger.error("Authentication failed, cannot proceed with booking")
            return

        # Parse booking parameters
        parsed_params = self.parse_command(command)

        # TODO: Implement booking execution logic
        # raise NotImplementedError("Booking execution not yet implemented")

    def _log_execution(self, command: str) -> None:
        """Log the execution of the booking scenario"""
        logger.info("Executing booking scenario with command: %s", command)
