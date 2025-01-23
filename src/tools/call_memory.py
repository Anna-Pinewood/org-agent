import logging
from typing import List
from src.tools.base import EnvTool, Tool, ToolResponse
from src.memory.interface import MemorySystem
from src.memory.models import UserPreference, ProblemSolution

logger = logging.getLogger(__name__)


class CallMemoryPrefTool(Tool):
    """Tool for retrieving user preferences from memory"""

    @property
    def description(self) -> str:
        return (
            "Use this tool when you're not certain "
            "about user preferences and need to look it up "
            "or past behavior that could help with the current situation. "
            "For example, checking preferred meeting rooms, post publication times, etc."
            "Parameters: search_query: str - the query of what to search for in memory if form: brief header like 'Room preference' and short question like 'Which rooms are commonly booked together?'"
        )

    async def execute(self,
                      memory_system: MemorySystem,
                      search_query: str) -> ToolResponse:
        """
        Search for relevant user preferences
        """
        try:
            preferences: List[UserPreference] = await memory_system.retrieve(
                context=search_query,
                collection="preferences"
            )

            if len(preferences) == 0:
                return ToolResponse(
                    success=True,
                    meta={
                        "result": None
                    }
                )
            return ToolResponse(
                success=True,
                meta={
                    "result": [pref.get_llm_format() for pref in preferences] if preferences else None
                }
            )

        except Exception as e:
            logger.error("Failed to retrieve preferences: %s", str(e))
            return ToolResponse(
                success=False,
                error=f"Failed to retrieve preferences: {str(e)}"
            )


class CallMemorySolutionsTool(EnvTool):
    """Tool for retrieving previous problem solutions from memory"""

    @ property
    def description(self) -> str:
        return ("Use this tool when encountering an error or problem to check if similar issues "
                "were successfully resolved in the past. Provides solution steps from previous experiences.")

    async def execute(
            self,
            memory_system: MemorySystem, search_query: str) -> ToolResponse:
        """
        Search for relevant problem solutions

        Args:
            search_query: Problem context to search for in memory

        Returns:
            ToolResponse with found solutions in meta['solutions'] or error if failed
        """
        try:
            solutions: List[ProblemSolution] = await memory_system.retrieve(
                context=search_query,
                collection="solutions"
            )

            return ToolResponse(
                success=True,
                meta={
                    "result": [sol.get_llm_format() for sol in solutions] if len(solutions) > 0 else None
                }
            )

        except Exception as e:
            logger.error("Failed to retrieve solutions: %s", str(e))
            return ToolResponse(
                success=False,
                error=f"Failed to retrieve solutions: {str(e)}"
            )
