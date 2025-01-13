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
            raise ValueError("Tool must be a subclass of Tool")
        self._tools[name] = tool

    def get_tool(self, name: str) -> Tool:
        return self._tools[name]

    def get_tools_description(self) -> Dict[str, str]:
        return {name: tool.description() for name, tool in self._tools.items()}


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

    # def __init__(__pydantic_self__, **data):
    #     # Preprocess the 'meta' field to convert lists into strings
    #     if "meta" in data:
    #         transformed_meta = {}
    #         for key, value in data["meta"].items():
    #             if isinstance(value, list):
    #                 transformed_meta[key] = ";\n".join(map(str, value))
    #             else:
    #                 transformed_meta[key] = value
    #         data["meta"] = transformed_meta
    #     super().__init__(**data)


@dataclass
class ToolExecutionRecord:
    """Record of a single tool execution within a step"""
    timestamp: datetime
    tool_name: str
    tool_params: Dict
    response: ToolResponse
    header_summary: str | None = None
    browser_state: dict | None = None

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
                        f"Result: {self.response.meta['narrative'][-1]}")

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

            if self.browser_state:
                error_details.append("Browser state at failure:")
                error_details.append(
                    f"  URL: {self.browser_state.get('url', 'N/A')}")
                visible_text = self.browser_state.get('visible_text') or "N/A"
                error_details.append(
                    f"  Some visible content:\n{visible_text}")

            if error_details:
                sections.append("\n".join(error_details))

        return "\n\n".join(sections)
