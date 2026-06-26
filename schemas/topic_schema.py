"""
Schemas for autonomous topic discovery and candidate generation.
"""

from typing import List
from pydantic import BaseModel, Field


class TopicCandidate(BaseModel):
    """
    Candidate topic idea with virality and classification details.
    """

    topic: str = Field(
        ...,
        description="Trending LinkedIn content topic.",
    )

    reason: str = Field(
        ...,
        description="Detailed rationale on why this topic is trending.",
    )

    niche: str = Field(
        ...,
        description="The technical sub-niche (e.g. AI Engineering, MLops, Architecture, Devops).",
    )

    base_score: float = Field(
        5.0,
        ge=1.0,
        le=10.0,
        description="Estimated engagement virality potential from 1.0 (low) to 10.0 (high).",
    )


class TopicDiscoveryOutput(BaseModel):
    """
    List of topic ideas discovered autonomously by the Topic Agent.
    """

    candidates: List[TopicCandidate] = Field(
        ...,
        description="List of trend candidate topic ideas.",
    )