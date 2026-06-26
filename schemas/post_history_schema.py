"""
Schemas for post history API endpoints.
"""

from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class GeneratedPostResponse(BaseModel):
    """
    Richer schema for returned posts history.
    """
    model_config = ConfigDict(from_attributes=True)

    id: int = Field(..., description="The database ID of the generated post.")
    topic: str = Field(..., description="Topic of the post.")
    topic_reason: str = Field(..., description="Why the topic was generated.")
    post_content: str = Field(..., description="The generated post content.")
    image_url: Optional[str] = Field(None, description="Optional URL of the DALL-E generated image.")
    image_prompt: Optional[str] = Field(None, description="Optional text prompt used to generate the image.")
    created_at: datetime = Field(..., description="Timestamp of post creation.")
