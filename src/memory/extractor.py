from datetime import datetime
import logging
from src.llm_interface import LLMInterface
from src.memory.models import ProblemSolution, UserPreference

logger = logging.getLogger(__name__)

EXTRACT_PREFERENCE_PROMPT = """Analyze the interaction context and extract user preferences or facts if they exist. Focus on discovering stated or implied preferences about rooms, timings, processes etc.

Context:
User command or dialog: {user_text}

If NO preferences are found, return null.
If preferences ARE found, return them in the following JSON structure:
{{
    "header": "Brief category name - e.g. Room preference, Time preference, Booking workflow preference",
    "text": "Complete fact in natural language that captures the preference context",
}}

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

EXTRACT_SOLUTION_PROMPT = """Analyze the execution history and extract key actions that solved the problem.

Context:
Execution history: {history}

Return solution details in the following JSON structure:
{{
    "problem_type": "Brief category like authentication_error, element_not_found, etc",
    "problem": "One line description of what went wrong",
    "key_actions": ["List of", "key steps", "that solved", "the problem"]
}}

Example output:
{{
    "problem_type": "element_not_found",
    "problem": "Submit button was not visible because page was not fully loaded",
    "key_actions": [
        "Waited for page load completion",
        "Scrolled to bottom of page",
        "Located and clicked submit button"
    ]
}}

Return only valid JSON without additional explanations."""


class PreferenceExtractor:
    """Extracts user preferences from interaction context using LLM analysis."""

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface
        self.extract_prompt = EXTRACT_PREFERENCE_PROMPT

    def extract(
        self,
        text: str,
        scenario_id: str,
    ) -> list[UserPreference] | None:
        """
        Extract preferences from text if they exist.

        Args:
            text: User input or interaction text to analyze
            scenario_id: ID of current scenario

        Returns:
            UserPreference if preference found, None otherwise
        """
        try:
            response = self.llm.send_request(
                prompt=self.extract_prompt,
                call_params={
                    "user_text": text,
                },
                response_format={"type": "json_object"}
            )

            extracted = self.llm.get_response_content(response)
            if not extracted:
                return None
            logger.info("Extracted preferences: %s", extracted)
            # Convert to UserPreference model with additional metadata
            return [
                UserPreference(
                    **extracted_single,
                    origins=text,
                    timestamp=datetime.now(),
                    scenario_id=scenario_id
                ) for extracted_single in extracted
            ]

        except Exception as e:
            logger.error(
                "Failed to extract preferences from text: %s",
                str(e)
            )
            return None


class SolutionExtractor:
    """Extracts successful problem solutions from execution history."""

    def __init__(self, llm_interface: LLMInterface):
        self.llm = llm_interface
        self.extract_prompt = EXTRACT_SOLUTION_PROMPT

    def extract(
        self,
        history: str,
        originar_error_msg: str,
        scenario_id: str,
    ) -> ProblemSolution | None:
        """
        Extract solution details from execution history.

        Args:
            history: Full execution history text
            problem_type: Category of the problem
            scenario_id: ID of current scenario

        Returns:
            ProblemSolution if extraction successful, None otherwise
        """
        try:
            response = self.llm.send_request(
                prompt=self.extract_prompt,
                call_params={
                    "history": history,
                },
                response_format={"type": "json_object"}
            )

            extracted = self.llm.get_response_content(response)
            if not extracted:
                return None

            return ProblemSolution(
                **extracted,
                originar_error_msg=originar_error_msg,
                steps=history.split("\n"),
                timestamp=datetime.now(),
                scenario_id=scenario_id
            )

        except Exception as e:
            logger.error(
                "Failed to extract solution from history: %s",
                str(e)
            )
            return None
