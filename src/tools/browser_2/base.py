
from abc import ABC, abstractmethod
from typing import Dict, TypedDict, Optional
from src.tools.base import Tool
from src.tools.browser_2.environment import BrowserEnvironment
from pydantic import BaseModel, Field
from typing import Dict, Optional


class BrowserToolResponse(BaseModel):
    """
    Standardized response format for browser tools
    """
    success: bool = Field(
        default=False,
        description="Indicates if the browser operation was successful"
    )
    error: Optional[str] = Field(
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
                    transformed_meta[key] = ", ".join(map(str, value))
                else:
                    transformed_meta[key] = value
            data["meta"] = transformed_meta
        super().__init__(**data)


class BrowserTool(Tool):
    """
    Base class for atomic browser operations.
    Tools don't store state - they receive environment and perform actions.
    """
    @abstractmethod
    async def execute(self,
                      env: BrowserEnvironment, **kwargs) -> BrowserToolResponse:
        """Execute single atomic operation on browser environment"""
        pass
