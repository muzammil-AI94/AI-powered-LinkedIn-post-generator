"""
Request schemas for API input validation.
"""

from typing import Optional
from pydantic import BaseModel, Field


class PostGenerationRequest(BaseModel):
    """
    Request schema for LinkedIn post generation.

    Optionally guides the generation with custom topic, audience, tone,
    and toggles image generation.
    """

    topic: Optional[str] = Field(
        default=None,
        min_length=5,
        max_length=300,
        description=(
            "Optional topic for LinkedIn post generation. "
            "If not provided, a trending topic is discovered autonomously."
        ),
    )

    audience: Optional[str] = Field(
        default="professionals",
        description="The target audience for the post (e.g. startup founders, junior engineers).",
    )

    tone: Optional[str] = Field(
        default="professional",
        description="The voice/tone of the post (e.g., educational, storytelling, witty, casual).",
    )

    generate_image: Optional[bool] = Field(
        default=False,
        description="Toggle to asynchronously generate a visual story image alongside the post.",
    )