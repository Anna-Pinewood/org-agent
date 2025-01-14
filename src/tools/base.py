from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
import logging
from typing import Any, Dict

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)


class Tool(ABC):
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        pass


class ToolBox:
    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    def register_tool(self, name: str, tool: Tool):
        if not isinstance(tool, Tool):

            raise ValueError(
                f"Tool must be a subclass of Tool, got {type(tool)}")
        self._tools[name] = tool

    def get_tool(self, name: str) -> Tool:
        return self._tools[name]

    def get_tools_description(self) -> Dict[str, str]:
        return {name: tool.description() for name, tool in self._tools.items()}

    def __contains__(self, name: str) -> bool:
        return name in self._tools


class ToolResponse(BaseModel):
    """
    Standardized response format for browser tools
    """
    success: bool = Field(
        default=False,
        description="Indicates if the tool operation was successful"
    )
    error: str | None = Field(
        default=None,
        description="Error message if operation failed"
    )
    meta: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dict with execution metadata for LLM reasoning"
    )


@dataclass
class ToolExecutionRecord:
    """Record of a single tool execution within a step"""
    timestamp: datetime
    tool_name: str
    tool_params: Dict
    response: ToolResponse
    header_summary: str | None = None
    env_params: dict | None = None

    def to_history_text(self) -> str:
        """
        Convert tool execution record to human-readable format for LLM analysis.
        Successful executions are summarized briefly while failures include more detail.

        Returns:
            str: Formatted history text suitable for LLM analysis
        """
        timestamp_str = self.timestamp.strftime("%Y-%m-%d %H:%M:%S")

        # Clean sensitive data from params
        safe_params = {
            k: "[REDACTED]" if k in ["password", "token", "secret"] else v
            for k, v in self.tool_params.items()
        }

        # Construct the status header
        status = "SUCCESS" if self.response.success else "FAILURE"
        if self.header_summary:
            status_header = f"{self.header_summary}: {status}"
        else:
            status_header = status

        # Base info included in all records
        base_info = (f"{status_header}\n"
                     f"Tool: {self.tool_name}\n"
                     f"Time: {timestamp_str}\n"
                     f"Parameters: {safe_params}")

        sections = [base_info]

        if self.response.success:
            # Brief successful execution summary
            meta_summary = []
            if "url" in self.response.meta:
                meta_summary.append(f"URL: {self.response.meta['url']}")
            if "narrative" in self.response.meta:
                if self.response.meta["narrative"]:
                    meta_summary.append(
                        f"How it ended: {self.response.meta['narrative'][-1]}")
            if "result" in self.response.meta:
                meta_summary.append(f"Result: {self.response.meta['result']}")
            # if other keys in meta, make logger warning

            for key, value in self.response.meta.items():
                if key not in ["url", "narrative"]:
                    logger.debug(
                        'The key "%s" won`t be included in the summary ("%s")',
                        key,
                        self.header_summary or "no header")

            if meta_summary:
                sections.append("\n".join(meta_summary))
        else:
            # Detailed failure information
            error_details = []
            error_details.append(f"Error: {self.response.error}")

            if "narrative" in self.response.meta:
                error_details.append("Execution steps:")
                for step in self.response.meta["narrative"]:
                    error_details.append(f"  - {step}")

            if self.env_params is None:
                return "\n\n".join(sections)

            error_details.append("State at failure:")
            for key, value in self.env_params.items():
                if value is not None:
                    error_details.append(f"  - {key}: {value}")

            if error_details:
                sections.append("\n".join(error_details))

        return "\n\n".join(sections)
