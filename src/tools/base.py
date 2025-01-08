from abc import ABC, abstractmethod
from datetime import datetime
import logging
from typing import Any, Dict

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
