from datetime import datetime, time
from pydantic import BaseModel, Field, model_validator
from scenarios.base import BaseScenario, ScenarioStep
import logging
from config import CONFIG
from src.message_broker import MessageBroker
from src.scenarios.booking.filling_form_step import RoomBookingStep
from src.scenarios.booking.login_step import LoginStep
from src.scenarios.booking.navigate_step import NavigateToBookingStep
from src.tools.browser.environment import BrowserEnvironment
from tools.date import CurrentDateTool, next_thursday
from llm_interface import LLMInterface
from pydantic.functional_validators import BeforeValidator
from typing import Annotated
from src.scenarios.prompts import ANALYZE_ERROR_PROMPT_BROWSER, ANALYZE_ERROR_PROMPT_BROWSER_MULTI

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
    room_numbers: list[str] | None = Field(
        description="List of preferred room numbers if specified", default=None)
    event_name: str = Field(
        description="Name of the event",
        default=default_booking_params.event_name)
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
    "room_numbers": [str] | null, # Extract room number mentions from the command, the number of mentions can be different from room count, if no mentions - null
    "event_name": str \ null,
    "date": "DD-MM-YYYY" | null, # You should calculate this based on the current date
    "start_time": "HH:MM" | null,
    "end_time": "HH:MM" | null,
    "building": string | null
}}

Return only valid JSON without comments or explanations.

Example input:
Current date: 07 January 2025, Tuesday
Command: "забронируй 3 аудитории на следующий четверг с 6 до 10 вечера на кронверкском проспекте, особенно 1405"

Example output:
{{
    "room_count": 3,
    "room_numbers": ["1405"],
    "event_name": null,
    "date": 09-01-2025",
    "start_time": "18:00",
    "end_time": "22:00",
    "building": "Кронверкский проспект"
}}"""


class BookingScenario(BaseScenario):
    """Scenario for handling room booking requests with authentication support"""

    def __init__(self,
                 message_broker: MessageBroker | None = None,
                 llm_brain: LLMInterface | None = None):
        super().__init__(llm_brain=llm_brain,
                         message_broker=message_broker)
        self.current_date = CurrentDateTool().execute()
        # Initialize steps
        self.steps = [
            LoginStep(),
            NavigateToBookingStep()
        ]
        # Initialize browser environment
        self.environment = BrowserEnvironment()
        self.analyze_error_prompt = ANALYZE_ERROR_PROMPT_BROWSER
        # self.analyze_error_prompt = ANALYZE_ERROR_PROMPT_BROWSER_MULTI
        

    def initialize_context(self, command: str, parsed_params: dict):
        super().initialize_context(command, parsed_params)

        # Add booking step for each room
        booking_steps = [
            RoomBookingStep(
                room_number=room,
                meta=parsed_params
            )
            for room in parsed_params['room_numbers']
        ]
        self.steps.extend(booking_steps)
        logger.info("Added booking steps in the scenario")

    async def execute(self, command: str) -> bool:
        """Execute the booking scenario"""
        # Initialize browser environment

        await self.environment.initialize()

        return await super().execute(command)

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

        logger.info("No booking intent detected")
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
        if parsed['room_numbers'] is None or len(parsed['room_numbers']) < parsed['room_count']:
            logger.info("Not all room numbers specified, adding default rooms")
            room_numbers_new = parsed['room_numbers'] or []
            possible_rooms = CONFIG.default_booking_params.preferred_rooms
            possible_rooms = [
                room for room in possible_rooms if room not in room_numbers_new]
            room_numbers_new.extend(
                possible_rooms[:parsed['room_count'] - len(room_numbers_new)])
            logger.info("Extended room numbers: %s", room_numbers_new)
            parsed['room_numbers'] = room_numbers_new

        result_clean = {key: value for key,
                        value in parsed.items() if value is not None}

        params = BookingParams(**result_clean)
        logger.info("Parsed booking parameters: %s", params)
        return params
