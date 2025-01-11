from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
import logging

from llm_interface import LLMInterface
from src.tools.base import ToolExecutionRecord, ToolResponse
from src.tools.browser.environment import BrowserEnvironment

logger = logging.getLogger(__name__)


class BaseScenario(ABC):
    """Base class for all scenarios"""

    def __init__(self, llm_brain: LLMInterface | None = None):
        if llm_brain is None:
            llm_brain = LLMInterface()
        self.llm_brain = llm_brain

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


class StepStatus(Enum):
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ScenarioStep:
    """Base class for scenario steps like LoginStep"""

    def __init__(self):
        self.execution_history: list[ToolExecutionRecord] = []
        self.status = StepStatus.IN_PROGRESS
        # Success criteria as list of required conditions
        self.success_criteria: list[dict] = []

    async def _record_tool_execution(
        self,
        tool_name: str,
        params: dict,
        response: ToolResponse,
        browser_env: BrowserEnvironment,
    ):
        """Record tool execution and capture browser state if error occurred"""
        browser_state = None
        if not response.success:
            # Get concise browser state description
            browser_state = {
                "url": browser_env.page.url,
                "visible_text": await browser_env.describe_state()
            }

        record = ToolExecutionRecord(
            timestamp=datetime.now(),
            tool_name=tool_name,
            tool_params=params,
            response=response,
            browser_state=browser_state
        )
        self.execution_history.append(record)

    async def verify_success(self, browser_env) -> bool:
        """Verify step completion based on success criteria"""
        raise NotImplementedError
