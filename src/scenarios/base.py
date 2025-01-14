from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
import logging

from llm_interface import LLMInterface
from src.scenarios.prompts import ANALYZE_ERROR_PROMPT_BASE
from src.tools.base import ToolBox, ToolExecutionRecord, ToolResponse
from src.tools.browser.environment import Environment
from pydantic import BaseModel

logger = logging.getLogger(__name__)


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
        self.toolbox = ToolBox()

    @abstractmethod
    def _register_tools(self):
        """Register available tools for this step"""
        pass

    async def _record_tool_execution(
            self,
            tool_name: str,
            params: dict,
            response: ToolResponse,
            environment: Environment,
            header_summary: str | None = None
    ) -> None:
        """Record tool execution and capture browser state if error occurred"""
        env_params = None
        if not response.success:
            # Get concise browser state description
            env_params = {
                "env_address": environment.current_state_address(),
                "env_state": await environment.describe_state()
            }

        record = ToolExecutionRecord(
            timestamp=datetime.now(),
            tool_name=tool_name,
            tool_params=params,
            response=response,
            env_params=env_params,
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

    @abstractmethod
    async def verify_success(self,
                             environment: Environment | None = None) -> bool:
        """Verify step completion based on success criteria"""
        pass

    @abstractmethod
    async def execute(self, **kwargs) -> bool:
        """Execute the step"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Human-readable description of what this step does"""
        pass


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
    MAX_CONSECUTIVE_RETRIES = 3  # Max times to retry same action with LLM
    MAX_TOTAL_RETRIES = 6  # Max total retries per step with LLM

    def __init__(
            self,
            llm_brain: LLMInterface | None = None):

        if llm_brain is None:
            llm_brain = LLMInterface()
        self.llm_brain = llm_brain
        self.context: ScenarioContext | None = None
        self.steps: list[ScenarioStep] = []
        self.environment = None
        # prompt with history and tool_descriptions variables
        self.analyze_error_prompt = ANALYZE_ERROR_PROMPT_BASE

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

    async def _handle_step_failure(self, current_step: ScenarioStep) -> bool:
        """
        Handle step failure by iteratively trying LLM-suggested recovery actions
        until success or stopping conditions met.

        Stopping conditions:
        - Same tool+params executed consecutively MAX_CONSECUTIVE_RETRIES times
        - Total retry attempts exceed MAX_TOTAL_RETRIES
        - Success criteria met

        Args:
            current_step: The failed step instance

        Returns:
            bool: True if recovery successful, False otherwise
        """
        logger.info("\nHandling failure for step %d",
                    self.context.current_step_index)

        total_retries = 0
        consecutive_same_actions = 1
        last_action = None  # Tuple of (tool_name, frozen_params)

        tool_descriptions = current_step.toolbox.get_tools_description()

        while total_retries < self.MAX_TOTAL_RETRIES:
            logger.info(
                "\n======\nRecovery attempt %d/%d",
                total_retries + 1, self.MAX_TOTAL_RETRIES
            )
            history = current_step.get_execution_history(
                include_successful=True)

            try:
                # Get LLM's analysis and next action
                response = self.llm_brain.send_request(
                    prompt=self.analyze_error_prompt,
                    call_params={
                        "history": history,
                        "tool_descriptions": tool_descriptions,
                    },
                    response_format={"type": "json_object"}
                )

                analysis = self.llm_brain.get_response_content(response)
                logger.info("LLM analysis: %s", analysis["analysis"])

                # Extract suggested action
                tool_name = analysis["next_action"]["tool_name"]
                tool_params = analysis["next_action"]["params"]

                # Check if tool exists
                if tool_name not in current_step.toolbox:
                    logger.error("LLM suggested unknown tool: %s", tool_name)
                    return False

                # Create frozen version of params for comparison
                current_action = (
                    tool_name,
                    frozenset(tool_params.items())
                )

                # Check if we're repeating the same action
                if current_action == last_action:
                    consecutive_same_actions += 1
                    if consecutive_same_actions >= self.MAX_CONSECUTIVE_RETRIES:
                        logger.warning(
                            "Stopping: Same action attempted %d times consecutively: %s %s",
                            consecutive_same_actions, tool_name, tool_params
                        )
                        return False
                else:
                    consecutive_same_actions = 1

                last_action = current_action

                # Execute suggested tool
                logger.info(
                    "Executing recovery action %d/%d - tool: %s, params: %s",
                    total_retries + 1, self.MAX_TOTAL_RETRIES,
                    tool_name, tool_params
                )

                tool = current_step.toolbox.get_tool(tool_name)
                if "environment" not in tool_params:
                    tool_params["env"] = self.environment
                result = await tool.execute(**tool_params)

                # Record tool execution
                await current_step._record_tool_execution(
                    tool_name=tool_name,
                    params=tool_params,
                    response=result,
                    environment=self.environment,
                    header_summary=f"Recovery attempt {total_retries + 1}"
                )

                # Check if step successful after this action
                if await current_step.verify_success(environment=self.environment):
                    logger.info(
                        "Recovery successful after %d attempts",
                        total_retries + 1
                    )
                    return True

                total_retries += 1

            except Exception as e:
                logger.error(
                    "Error during recovery attempt %d: %s",
                    total_retries + 1, str(e)
                )
                return False

        logger.warning(
            "Stopping: Maximum total retries (%d) exceeded",
            self.MAX_TOTAL_RETRIES
        )
        return False

    async def execute(self, command: str) -> bool:
        """Main execution flow"""
        logger.info("Starting scenario %s execution for command: %s",
                    self.__class__.__name__, command)

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
                    "\nExecuting step %d: %s",
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
                    # Attempt recovery
                    recovery_success = await self._handle_step_failure(current_step)
                    if not recovery_success:
                        logger.error(
                            "Step %d failed and recovery unsuccessful",
                            self.context.current_step_index
                        )
                        return False

                    logger.info(
                        "Recovery successful for step %d",
                        self.context.current_step_index
                    )
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
