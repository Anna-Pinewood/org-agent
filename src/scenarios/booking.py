from scenarios.base import BaseScenario
import logging

logger = logging.getLogger(__name__)


class BookingScenario(BaseScenario):
    """Scenario for handling room booking requests"""

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
                logger.info(f"Booking intent detected with stem '{stem}'")
                return 1.0

        logger.debug("No booking intent detected")
        return 0.0

    def execute(self, command: str) -> None:
        """
        Execute the booking scenario
        Args:
            command: User's natural language command
        """
        self._log_execution(command)
        # TODO: Implement booking execution logic
        raise NotImplementedError("Booking execution not yet implemented")
