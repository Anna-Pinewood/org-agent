
from abc import ABC, abstractmethod
from typing import TypedDict, Optional
from src.tools.base import EnvTool
from src.tools.base import ToolResponse
from src.tools.browser.environment import BrowserEnvironment
from typing import Optional


class BrowserTool(EnvTool):
    """
    Base class for atomic browser operations.
    Tools don't store state - they receive environment and perform actions.
    """
    @abstractmethod
    async def execute(self,
                      env: BrowserEnvironment, **kwargs) -> ToolResponse:
        """Execute single atomic operation on browser environment"""
        pass
