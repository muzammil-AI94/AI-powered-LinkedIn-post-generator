"""
Response schemas for API responses.

Defines standardized API response contracts between Frontend and Backend.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class LinkedInPostResponse(BaseModel):
    """
    Final LinkedIn post response.
    """

    post: str = Field(
        ...,
        description="Generated LinkedIn post content.",
    )

    topic: str = Field(
        default="",
        description="Topic the post was generated about.",
    )

    topic_reason: str = Field(
        default="",
        description="Why this topic was selected.",
    )

    image_url: Optional[str] = Field(
        default=None,
        description="DALL-E image URL if generated.",
    )


class TaskCreationResponse(BaseModel):
    """
    Initial response returned immediately when a workflow generation is queued.
    """

    task_id: str = Field(
        ...,
        description="The unique Celery task correlation ID.",
    )

    status: str = Field(
        "queued",
        description="The initial queue status of the asynchronous task.",
    )


class TaskStatusResponse(BaseModel):
    """
    Highly structured polling state for tracking workflow execution stage.
    """

    task_id: str = Field(
        ...,
        description="The unique task identifier.",
    )

    status: str = Field(
        ...,
        description="Overall status of execution (queued, processing, success, failure).",
    )

    stage: Optional[str] = Field(
        default=None,
        description="Current stage in the multi-agent graph execution (e.g. RESEARCHING, GENERATING).",
    )

    post_id: Optional[int] = Field(
        default=None,
        description="Database primary ID of the generated post record.",
    )

    post: Optional[str] = Field(
        default=None,
        description="Generated post content once completed.",
    )

    image_url: Optional[str] = Field(
        default=None,
        description="Generated image URL once completed.",
    )

    error: Optional[str] = Field(
        default=None,
        description="Details of any runtime exception occurred.",
    )


class PostHistoryItem(BaseModel):
    """
    Single post record returned in paginated post history responses.
    """

    id: int = Field(
        ...,
        description="Database primary key of the post.",
    )

    topic: str = Field(
        ...,
        description="Topic the post was generated about.",
    )

    topic_reason: str = Field(
        ...,
        description="Why this topic was selected by the agent.",
    )

    post_content: str = Field(
        ...,
        description="Full generated LinkedIn post text.",
    )

    niche: Optional[str] = Field(
        default=None,
        description="Niche classification for the post.",
    )

    engagement_score: Optional[float] = Field(
        default=None,
        description="Predicted engagement/virality score.",
    )

    image_url: Optional[str] = Field(
        default=None,
        description="DALL-E generated image URL if available.",
    )

    image_prompt: Optional[str] = Field(
        default=None,
        description="Image generation prompt used for DALL-E.",
    )

    created_at: str = Field(
        ...,
        description="ISO 8601 timestamp of post creation.",
    )


class PostHistoryResponse(BaseModel):
    """
    Paginated response containing a list of generated posts with metadata.
    """

    posts: List[PostHistoryItem] = Field(
        ...,
        description="List of post records for the current page.",
    )

    total: int = Field(
        ...,
        description="Total number of posts in the database.",
    )

    limit: int = Field(
        ...,
        description="Maximum number of posts returned per page.",
    )

    offset: int = Field(
        ...,
        description="Number of posts skipped from the beginning.",
    )


class PostDeleteResponse(BaseModel):
    """
    Confirmation response after deleting a post record.
    """

    deleted: bool = Field(
        ...,
        description="Whether the post was successfully deleted.",
    )

    post_id: int = Field(
        ...,
        description="Database ID of the deleted post.",
    )