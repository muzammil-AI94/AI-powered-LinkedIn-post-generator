"""
Database model for generated LinkedIn posts.
"""

from datetime import datetime, timezone
from typing import Any, List, Optional

from sqlalchemy import DateTime, Integer, String, Text, JSON
from sqlalchemy.orm import Mapped, mapped_column

from app.db.database import Base
from app.core.config import settings

# Determine if Database backend is SQLite vs. Postgres
is_sqlite = settings.DATABASE_URL.startswith("sqlite")

if is_sqlite:
    # Use JSON column to store float array in SQLite
    EmbeddingType = JSON
else:
    from pgvector.sqlalchemy import Vector
    # text-embedding-3-small uses 1536 dimensions
    EmbeddingType = Vector(1536)


class GeneratedPost(Base):
    """
    Persisted generated LinkedIn post with metadata and semantic vector embedding.
    """

    __tablename__ = "generated_posts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        index=True,
    )

    topic: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    topic_reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    post_content: Mapped[str] = mapped_column(
        Text,
        nullable=False,
    )

    # Niche classification for structural content mapping
    niche: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
    )

    # Engagement and virality prediction scores
    engagement_score: Mapped[Optional[float]] = mapped_column(
        nullable=True,
    )

    # Embedding vector for semantic duplicate detection and retrieval
    embedding: Mapped[Optional[List[float]]] = mapped_column(
        EmbeddingType,
        nullable=True,
    )

    # Optional Generated DALL-E Image URL and generated visual art prompt
    image_url: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    image_prompt: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
    )