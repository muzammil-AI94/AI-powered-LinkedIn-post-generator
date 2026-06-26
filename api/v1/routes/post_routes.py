"""
API routes for LinkedIn post generation and real-time task stage monitoring.

Exposes endpoints for queueing generation workflows and polling their execution states.
"""

from typing import List, Optional
from celery.result import AsyncResult
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.db.database import AsyncSessionLocal
from app.db.models.post_model import GeneratedPost
from app.schemas.request_schema import (
    PostGenerationRequest,
)
from app.schemas.response_schema import (
    PostDeleteResponse,
    PostHistoryItem,
    PostHistoryResponse,
    TaskCreationResponse,
    TaskStatusResponse,
)
from app.utils.cache import cache
from app.workers.celery_app import celery_app
from app.workers.workflow_tasks import execute_linkedin_workflow

router = APIRouter()


async def get_db_session() -> AsyncSession:
    """
    Dependency: yield an async DB session per request.
    """
    async with AsyncSessionLocal() as session:
        yield session


@router.post(
    "/generate-post",
    response_model=TaskCreationResponse,
    summary="Queue LinkedIn Post Generation Task",
    description=(
        "Enqueues an asynchronous, distributed Celery task to run "
        "the multi-agent LangGraph generation workflow. Returns task_id immediately."
    ),
)
async def generate_post(
    request: PostGenerationRequest | None = None,
) -> TaskCreationResponse:
    """
    Queue autonomous LinkedIn generation workflow.
    """
    logger.info("post_generation_request_received")

    # Resolve default parameters if request body is empty
    topic = request.topic if request else None
    audience = request.audience if request else "professionals"
    tone = request.tone if request else "professional"
    generate_image = request.generate_image if request else False

    try:
        # 1. Enqueue task asynchronously to Celery worker (non-blocking queue)
        task = execute_linkedin_workflow.delay(
            topic=topic,
            audience=audience,
            tone=tone,
            generate_image=generate_image,
        )

        logger.info(
            "post_generation_task_queued",
            task_id=task.id,
            topic=topic,
        )

        return TaskCreationResponse(
            task_id=task.id,
            status="queued",
        )

    except Exception as error:
        logger.error(
            "post_generation_queuing_failed",
            error=str(error),
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to enqueue autonomous generation task.",
        ) from error


@router.get(
    "/tasks/{task_id}",
    response_model=TaskStatusResponse,
    summary="Poll Task Status and Stage Progress",
    description=(
        "Queries the real-time execution state of the workflow. "
        "Returns current agent progress and draft content as soon as it becomes available."
    ),
)
async def get_task_status(
    task_id: str,
    session: AsyncSession = Depends(get_db_session),
) -> TaskStatusResponse:
    """
    Poll task stage progress, Celery statuses, and intermediate/final content.
    """
    logger.debug("polling_task_status", task_id=task_id)

    # 1. Query Celery execution state
    res = AsyncResult(task_id, app=celery_app)
    celery_state = res.state

    # 2. Query real-time workflow stage progress from Redis cache
    stage_val = await cache.get(f"task_stage:{task_id}")
    stage = str(stage_val) if stage_val else None

    # Handle standard Celery failures
    if celery_state == "FAILURE":
        return TaskStatusResponse(
            task_id=task_id,
            status="failure",
            stage=stage or "FAILED",
            error=str(res.result) or "Unknown Celery error.",
        )

    # Check if task is still in queued state
    if celery_state in ("PENDING", "RECEIVED", "RETRY"):
        return TaskStatusResponse(
            task_id=task_id,
            status="queued",
            stage=stage or "QUEUED",
        )

    # Check database for generated post content (to support progressive text delivery)
    post_id = None
    post_content = None
    image_url = None

    # If the Celery task finished successfully (meaning text is ready)
    if celery_state == "SUCCESS" and res.result:
        task_res = res.result
        if isinstance(task_res, dict) and task_res.get("status") == "success":
            post_id = task_res.get("post_id")

            # Query database to grab content
            if post_id:
                db_result = await session.execute(
                    select(GeneratedPost).where(GeneratedPost.id == post_id)
                )
                db_post = db_result.scalar_one_or_none()
                if db_post:
                    post_content = db_post.post_content
                    image_url = db_post.image_url

    # Map real-time status returned to Frontend
    if stage == "COMPLETED":
        return TaskStatusResponse(
            task_id=task_id,
            status="success",
            stage="COMPLETED",
            post_id=post_id,
            post=post_content,
            image_url=image_url,
        )

    elif stage == "FAILED":
        return TaskStatusResponse(
            task_id=task_id,
            status="failure",
            stage="FAILED",
            error="Agent workflow crashed.",
        )

    # In all other cases, task is actively processing (with intermediate text if image is still generating)
    return TaskStatusResponse(
        task_id=task_id,
        status="processing",
        stage=stage or "PROCESSING",
        post_id=post_id,
        post=post_content,
        image_url=image_url,
    )


@router.get(
    "/history",
    response_model=PostHistoryResponse,
    summary="Paginated Post History",
    description=(
        "Returns a paginated list of all generated LinkedIn posts, "
        "ordered by creation date descending (newest first)."
    ),
)
async def get_post_history(
    limit: int = 10,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> PostHistoryResponse:
    """
    Retrieve paginated post history from the database.
    """
    logger.debug("fetching_post_history", limit=limit, offset=offset)

    # Count total posts for pagination metadata
    count_result = await session.execute(
        select(func.count()).select_from(GeneratedPost)
    )
    total = count_result.scalar_one()

    # Fetch paginated post records ordered by newest first
    result = await session.execute(
        select(GeneratedPost)
        .order_by(GeneratedPost.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    posts = result.scalars().all()

    # Serialize to response schema with ISO datetime strings
    post_items = [
        PostHistoryItem(
            id=post.id,
            topic=post.topic,
            topic_reason=post.topic_reason,
            post_content=post.post_content,
            niche=post.niche,
            engagement_score=post.engagement_score,
            image_url=post.image_url,
            image_prompt=post.image_prompt,
            created_at=post.created_at.isoformat(),
        )
        for post in posts
    ]

    return PostHistoryResponse(
        posts=post_items,
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/{post_id}",
    response_model=PostHistoryItem,
    summary="Get Single Post",
    description="Retrieve a single generated post by its database ID.",
)
async def get_post(
    post_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> PostHistoryItem:
    """
    Retrieve a single post record by ID.
    """
    logger.debug("fetching_single_post", post_id=post_id)

    result = await session.execute(
        select(GeneratedPost).where(GeneratedPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=404,
            detail=f"Post with id {post_id} not found.",
        )

    return PostHistoryItem(
        id=post.id,
        topic=post.topic,
        topic_reason=post.topic_reason,
        post_content=post.post_content,
        niche=post.niche,
        engagement_score=post.engagement_score,
        image_url=post.image_url,
        image_prompt=post.image_prompt,
        created_at=post.created_at.isoformat(),
    )


@router.delete(
    "/{post_id}",
    response_model=PostDeleteResponse,
    summary="Delete a Post",
    description="Permanently delete a generated post record from the database.",
)
async def delete_post(
    post_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> PostDeleteResponse:
    """
    Hard delete a post record by ID.
    """
    logger.debug("deleting_post", post_id=post_id)

    result = await session.execute(
        select(GeneratedPost).where(GeneratedPost.id == post_id)
    )
    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=404,
            detail=f"Post with id {post_id} not found.",
        )

    await session.delete(post)
    await session.commit()

    logger.info("post_deleted", post_id=post_id)

    return PostDeleteResponse(
        deleted=True,
        post_id=post_id,
    )