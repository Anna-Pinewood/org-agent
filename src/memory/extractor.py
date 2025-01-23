from datetime import datetime
import logging
from src.llm_interface import LLMInterface
from src.memory.models import UserPreference

logger = logging.getLogger(__name__)

EXTRACT_PREFERENCE_PROMPT = """Analyze the interaction context and extract user preferences or facts if they exist. Focus on discovering stated or implied preferences about rooms, timings, processes etc.

Context:
User command or dialog: {user_text}
Scenario type: {scenario_type}

If NO preferences are found, return null.
If preferences ARE found, return them in the following JSON structure:
{
    "header": "Brief category name - e.g. Room preference, Time preference, Booking workflow preference",
    "text": "Complete fact in natural language that captures the preference context",
}

Examples:

Input: "Мне нужна аудитория 1405, но пойдёт и 1404, они рядом находятся"
Output: [
    {{
        "header": "Room preference",
        "text": "User prefers room 1404, with room 1405 as acceptable alternative due to proximity",
    }},
    {{
        "header": "Rooms proximity",
        "text": "Rooms 1404 and is located near room 1405",    
    }}
]

Input: "Can you book a room for next Thursday?"
Output: null

Return only valid JSON or null without additional explanations."""


class PreferenceExtractor:
    """Extracts user preferences from interaction context using LLM analysis."""

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface
        self.extract_prompt = EXTRACT_PREFERENCE_PROMPT

    async def extract(
        self,
        text: str,
        scenario_id: str,
        scenario_type: str
    ) -> UserPreference | None:
        """
        Extract preferences from text if they exist.

        Args:
            text: User input or interaction text to analyze
            scenario_id: ID of current scenario
            scenario_type: Type of scenario (booking, moderation etc)

        Returns:
            UserPreference if preference found, None otherwise
        """
        try:
            response = await self.llm.send_request(
                prompt=self.extract_prompt,
                call_params={
                    "user_text": text,
                    "scenario_type": scenario_type
                },
                response_format={"type": "json_object"}
            )

            extracted = self.llm.get_response_content(response)
            if not extracted:
                return None

            # Convert to UserPreference model with additional metadata
            return UserPreference(
                **extracted,
                origins=text,
                timestamp=datetime.now(),
                scenario_id=scenario_id
            )

        except Exception as e:
            logger.error(
                "Failed to extract preferences from text: %s",
                str(e)
            )
            return None
