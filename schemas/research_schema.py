"""
Schemas for research agent outputs.

Why this module exists:
------------------------
Defines deterministic structured outputs
for the Research Agent.

Structured outputs reduce:
- hallucinations
- parsing failures
- orchestration instability
"""

from pydantic import BaseModel, Field


class ResearchOutput(BaseModel):
    """
    Structured output from the Research Agent.
    """

    topic_summary: str = Field(
        ...,
        description="Short summary of the topic.",
    )

    key_points: list[str] = Field(
        ...,
        description="Main insights about the topic.",
    )

    hooks: list[str] = Field(
        ...,
        description="Potential LinkedIn hooks.",
    )

    audience_pain_points: list[str] = Field(
        ...,
        description="Audience pain points related to topic.",
    )