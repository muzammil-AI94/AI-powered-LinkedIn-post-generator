"""
API routes for retrieving generated LinkedIn posts.

Responsibilities:
-----------------
- list all generated posts (paginated)
- retrieve a single post by ID
- return structured post history
"""

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.db.database import AsyncSessionLocal
from app.db.models.post_model import GeneratedPost
from app.schemas.post_history_schema import (
    GeneratedPostResponse,
)

router = APIRouter()


async def get_db_session() -> AsyncSession:
    """
    Dependency: yield an async DB session per request.
    """

    async with AsyncSessionLocal() as session:
        yield session


@router.get(
    "/posts",
    response_model=List[GeneratedPostResponse],
    summary="List Generated Posts",
    description="Retrieve all previously generated LinkedIn posts, newest first.",
)
async def list_posts(
    limit: int = 20,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> List[GeneratedPostResponse]:
    """
    List all generated LinkedIn posts.

    Args:
        limit:   Maximum number of posts to return (default 20).
        offset:  Number of posts to skip for pagination.
        session: Injected database session.

    Returns:
        List of generated post records.
    """

    logger.info("list_posts_requested", limit=limit, offset=offset)

    result = await session.execute(
        select(GeneratedPost)
        .order_by(GeneratedPost.created_at.desc())
        .limit(limit)
        .offset(offset)
    )

    posts = result.scalars().all()

    return [
        GeneratedPostResponse.model_validate(post)
        for post in posts
    ]


@router.get(
    "/posts/{post_id}",
    response_model=GeneratedPostResponse,
    summary="Get Post By ID",
    description="Retrieve a single generated LinkedIn post by its ID.",
)
async def get_post(
    post_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> GeneratedPostResponse:
    """
    Retrieve a single LinkedIn post by ID.

    Args:
        post_id: Database ID of the post.
        session: Injected database session.

    Returns:
        Generated post record.

    Raises:
        404 if post not found.
    """

    logger.info("get_post_requested", post_id=post_id)

    result = await session.execute(
        select(GeneratedPost).where(
            GeneratedPost.id == post_id
        )
    )

    post = result.scalar_one_or_none()

    if not post:
        raise HTTPException(
            status_code=404,
            detail=f"Post with id={post_id} not found.",
        )

    return GeneratedPostResponse.model_validate(post)
