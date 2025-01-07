from abc import ABC, abstractmethod
import logging

logger = logging.getLogger(__name__)


class BaseScenario(ABC):
    """Base class for all scenarios"""

    @abstractmethod
    def classify_intent(self, command: str) -> float:
        """
        Determine how well this scenario matches the given command
        Args:
            command: User's natural language command
        Returns:
            float: Score between 0 and 1, where 1 means perfect match
        """
        pass

    @abstractmethod
    def execute(self, command: str) -> None:
        """
        Execute the scenario with the given command
        Args:
            command: User's natural language command
        Raises:
            Exception: If execution fails
        """
        pass

    def _log_execution(self, command: str) -> None:
        """Helper to log execution attempts"""
        logger.info(
            f"Executing {self.__class__.__name__} with command: {command}"
        )
