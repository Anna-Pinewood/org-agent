from datetime import datetime
from typing import List
from pydantic import BaseModel, Field


class UserPreference(BaseModel):
    origins: str = Field(
        description="Original message from which this fact was retrieved (or string like f'{llm question} {user's answer}' if CallHumanTool was triggered.)")
    header: str = Field(
        description="E.g., 'Room preference', 'Booking note', 'Post publication time' – briefly how can fact be described briedly")
    text: str = Field(
        description="Fact text e.g. 'Rooms 1404, 1405 are commonly booked together, since they are close to each other.'")
    # times_mentioned: int = Field(
    #     description="How many times was this fact mentioned. For example how often did user booked certain room."
    # )
    timestamp: str = Field(description="When this preference was learned")
    scenario_id: str = Field(
        description="Which scenario surfaced this preference")

    def get_llm_format(self) -> str:
        """Format preference data for LLM analysis"""
        return f"{self.header}\n{self.text}"


class ProblemSolution(BaseModel):
    problem_type: str = Field(
        description="E.g. 'authentication_error', 'booking_conflict'")
    originar_error_msg: str = Field(
        description="The error signature that identifies this problem")
    steps: List[str] = Field(description="All sollution steps (basially logs)")
    problem: str = Field(
        description="Natural language problem description in one line. What happened? Room 1405 was already booked. Login wasn't successful.")
    key_actions: list[str] = Field(
        description="Only key actions to solve this problem (LLM rertieves them after problem solved)")
    timestamp: str = Field(description="When this preference was learned")
    scenario_id: str = Field(
        description="Which scenario surfaced this preference")

    @property
    def text(self) -> str:
        return "\n".join(self.steps)

    def get_llm_format(self) -> str:
        """Format solution data for LLM analysis"""
        return f"""Type: {self.problem_type}
Error: {self.originar_error_msg}
Problem: {self.problem}
Key actions: {', '.join(self.key_actions)}"""
