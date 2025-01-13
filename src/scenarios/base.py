from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from llm_interface import LLMInterface
from src.tools.base import ToolExecutionRecord, ToolResponse
from src.tools.browser.environment import BrowserEnvironment
from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ScenarioStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    WAITING_FOR_CLARIFICATION = "waiting_for_clarification"


@dataclass
class ScenarioContext:
    """Holds the context of scenario execution"""
    original_command: str
    parsed_params: dict  # Scenario-specific parsed parameters
    current_step_index: int = 0
    status: ScenarioStatus = ScenarioStatus.NOT_STARTED
    error_context: dict | None = None  # Details about current error if any


class BaseScenario(ABC):
    """Base class for all scenarios"""

    def __init__(
            self,
            llm_brain: LLMInterface | None = None):

        if llm_brain is None:
            llm_brain = LLMInterface()
        self.llm_brain = llm_brain
        self.context: ScenarioContext | None = None
        self.steps: list[ScenarioStep] = []

    def initialize_context(self, command: str, parsed_params: dict):
        self.context = ScenarioContext(
            original_command=command,
            parsed_params=parsed_params
        )

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
    def parse_command(self, command: str) -> BaseModel:
        """Parse natural language command into structured parameters"""
        pass

    async def execute(self, command: str) -> bool:
        """Main execution flow"""
        logger.info("Starting scenario execution for command: %s", command)

        # Parse command and initialize context
        parsed_params = self.parse_command(command)
        self.initialize_context(
            command=command,
            parsed_params=parsed_params.model_dump())
        self.context.status = ScenarioStatus.IN_PROGRESS

        try:
            # Execute steps sequentially
            while self.context.current_step_index < len(self.steps):
                current_step = self.steps[self.context.current_step_index]
                logger.info(
                    "Executing step %d: %s",
                    self.context.current_step_index,
                    current_step.__class__.__name__
                )

                # Execute step
                success = await self._execute_step(current_step)

                if not success:
                    # Step failed, need clarification
                    self.context.status = ScenarioStatus.WAITING_FOR_CLARIFICATION

                    # Here we'll later implement:
                    # 1. LLM analysis of failure
                    # 2. User interaction
                    # 3. Execution of corrective actions
                    # For now just fail
                    logger.error(
                        "Step %d failed, scenario needs clarification",
                        self.context.current_step_index
                    )
                    return False

                # Step succeeded, move to next
                self.context.current_step_index += 1

            # All steps completed successfully
            self.context.status = ScenarioStatus.COMPLETED
            return True

        except Exception as e:
            logger.error("Scenario execution failed: %s", str(e))
            self.context.status = ScenarioStatus.FAILED
            return False

    def _log_execution(self, command: str) -> None:
        """Helper to log execution attempts"""
        logger.info(
            f"Executing {self.__class__.__name__} with command: {command}"
        )


class StepStatus(Enum):
    NOT_STARTED = "not_started"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    RETRYING = "retrying"


class ScenarioStep:
    """Set of tools executed in a sequence to accomplish a scenario step"""

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
            header_summary: str | None = None) -> None:
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
            browser_state=browser_state,
            header_summary=header_summary
        )
        self.execution_history.append(record)

    def get_execution_history(self, include_successful: bool = True) -> str:
        """
            Generate a comprehensive history of all tool executions in this step.

            Args:
                include_successful: Whether to include successful executions in the output.
                                Failed executions are always included.

            Returns:
                str: Formatted history text suitable for LLM analysis
    """
        if not self.execution_history:
            return "No execution history available."

        history_sections = []

        # Add step metadata
        history_sections.append(f"Step Status: {self.status.value}")
        history_sections.append(
            f"Total executions: {len(self.execution_history)}")

        # Calculate success rate
        successful = sum(1 for record in self.execution_history
                         if record.response.success)
        success_rate = (successful / len(self.execution_history)) * 100
        history_sections.append(f"Success rate: {success_rate:.1f}%")

        # Add individual execution records
        history_sections.append("\nExecution Records:")
        for idx, record in enumerate(self.execution_history, 1):
            if record.response.success and not include_successful:
                continue

            history_sections.append(f"\n--- Sub-command #{idx} ---")
            history_sections.append(record.to_history_text())

        return "\n".join(history_sections)

    async def verify_success(self, **kwargs) -> bool:
        """Verify step completion based on success criteria"""
        raise NotImplementedError

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this step does"""
        pass
