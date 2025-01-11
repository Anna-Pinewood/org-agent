from abc import ABC, abstractmethod
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
    meta: Dict[str, str] = Field(
        default_factory=dict,
        description="Dict with execution metadata for LLM reasoning"
    )

    def __init__(__pydantic_self__, **data):
        # Preprocess the 'meta' field to convert lists into strings
        if "meta" in data:
            transformed_meta = {}
            for key, value in data["meta"].items():
                if isinstance(value, list):
                    transformed_meta[key] = ";\n".join(map(str, value))
                else:
                    transformed_meta[key] = value
            data["meta"] = transformed_meta
        super().__init__(**data)


class ToolExecutionRecord:
    """Record of a single tool execution within a step"""
    timestamp: datetime
    tool_name: str
    tool_params: Dict
    response: ToolResponse
    # Brief browser state captured only on error
    browser_state: dict | None = None
