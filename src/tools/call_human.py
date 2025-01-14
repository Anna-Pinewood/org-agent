import logging
import asyncio
from message_broker import MessageBroker
from typing import Optional, List
from dataclasses import dataclass
from src.tools.base import Tool, ToolResponse

logger = logging.getLogger(__name__)


class CallHumanTool(Tool):
    """Tool for requesting human assistance when LLM is uncertain"""

    async def execute(
        self,
        broker: MessageBroker,
        question_to_human: str,
        options: list[str] | None = None,
        scenario_id: str | None = None,
        timeout: int = 300  # Timeout in seconds
    ) -> ToolResponse:
        """Execute the human call tool to get user input

        Args:
            broker: Message broker instance for communication
            question_to_human: Question to ask the human
            options: Optional list of valid response options
            scenario_id: Optional scenario identifier
            timeout: Timeout in seconds (default 300s = 5min)

        Returns:
            ToolResponse containing success status and response
        """
        try:
            # Send request and get request_id
            request_id = await broker.send_request(
                scenario_id=scenario_id,
                question=question_to_human,
                options=options,
            )
            logger.info("Sent human request %s", request_id)

            # Wait for response with timeout
            start_time = asyncio.get_event_loop().time()
            while True:
                # Check if we've exceeded timeout
                if asyncio.get_event_loop().time() - start_time > timeout:
                    logger.error(
                        "Timeout waiting for human response to question: %s",
                        question_to_human
                    )
                    return ToolResponse(
                        success=False,
                        error="Timeout waiting for human response",
                        meta={"request_id": request_id}
                    )

                # Try to get response
                response = await broker.get_response(request_id)
                if response is not None:
                    logger.info("Got human response for request %s: %s",
                                request_id, response)
                    return ToolResponse(
                        success=True,
                        meta={
                            "request_id": request_id,
                            # "narrative": [f'Human answered: "{response}"']
                            "result": f'Human answered: "{response}"'
                        }
                    )

                # Wait a bit before checking again
                await asyncio.sleep(0.1)

        except Exception as e:
            logger.error("Error getting human response: %s", str(e))
            return ToolResponse(
                success=False,
                error=f"Failed to get human response: {str(e)}"
            )

    def description(self) -> str:
        return """Request human assistance with decisions or clarifications.
Use this tool when:
- Uncertain about correct action
- Need approval for critical steps 
- Multiple valid options exist
- Unexpected errors without clear resolution
- Additional context/information needed

Args:
- question_to_human: Specific question for human to answer, give a little context
- options: List of possible choices if applicable or None
"""
