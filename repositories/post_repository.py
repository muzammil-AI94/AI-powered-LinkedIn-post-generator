"""
Repository class for managing database operations for GeneratedPost.
"""

from typing import List, Optional
import numpy as np
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.models.post_model import GeneratedPost
from app.repositories.base import BaseRepository


class PostRepository(BaseRepository[GeneratedPost]):
    """
    Repository for GeneratedPost ORM operations with fallback vector capabilities.
    """

    def __init__(self) -> None:
        super().__init__(GeneratedPost)

    async def get_by_topic(
        self,
        db_session: AsyncSession,
        topic: str,
    ) -> Optional[GeneratedPost]:
        """
        Retrieve a post by exact topic string match.
        """
        query = select(self.model).where(self.model.topic == topic)
        result = await db_session.execute(query)
        return result.scalar_one_or_none()

    async def find_similar_by_embedding(
        self,
        db_session: AsyncSession,
        embedding: List[float],
        threshold: float = 0.85,
        limit: int = 5,
    ) -> List[tuple[GeneratedPost, float]]:
        """
        Perform semantic similarity search on posts using embeddings.

        If PostgreSQL is selected, uses the pgvector native cosine distance operator.
        If SQLite is selected, retrieves posts and calculates similarity using NumPy.
        """
        is_sqlite = settings.DATABASE_URL.startswith("sqlite")

        if not is_sqlite:
            # Native Postgres pgvector cosine distance: <=> operator
            # Cosine similarity = 1 - cosine distance
            cosine_distance = self.model.embedding.cosine_distance(embedding)
            query = (
                select(self.model, (1 - cosine_distance).label("similarity"))
                .where((1 - cosine_distance) >= threshold)
                .order_by(cosine_distance)
                .limit(limit)
            )
            result = await db_session.execute(query)
            return [(row[0], float(row[1])) for row in result.all()]

        # SQLite Fallback: Fetch all posts containing embeddings and compute in memory using numpy
        query = select(self.model).where(self.model.embedding.isnot(None))
        result = await db_session.execute(query)
        all_posts = result.scalars().all()

        query_vector = np.array(embedding)
        norm_query = np.linalg.norm(query_vector)

        if norm_query == 0:
            return []

        scored_posts = []
        for post in all_posts:
            # Under SQLite, the embedding field stores JSON deserialized lists automatically
            if not post.embedding:
                continue

            post_vector = np.array(post.embedding)
            norm_post = np.linalg.norm(post_vector)

            if norm_post == 0:
                continue

            # Cosine similarity formula
            similarity = np.dot(query_vector, post_vector) / (norm_query * norm_post)
            if similarity >= threshold:
                scored_posts.append((post, float(similarity)))

        # Sort descending by similarity score
        scored_posts.sort(key=lambda x: x[1], reverse=True)
        return scored_posts[:limit]


post_repository = PostRepository()
