"""
Business service for managing agent long-term vector memory.

Uses embeddings to identify semantic duplicates, store generated content,
and retrieve historical topics.
"""

from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.repositories.post_repository import post_repository
from app.utils.embeddings import embedding_service


class MemoryService:
    """
    Service coordinating semantic queries and vector memory persistence.
    """

    async def get_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a given text.
        """
        return await embedding_service.generate_embedding(text)

    async def check_semantic_duplicate(
        self,
        db_session: AsyncSession,
        topic: str,
        threshold: float = 0.85,
    ) -> Optional[str]:
        """
        Check if a similar topic was already processed using vector similarity.

        Returns:
            The topic text of the matching duplicate, or None if unique.
        """
        logger.info("checking_semantic_duplicates", topic=topic)

        # Generate query vector
        embedding = await self.get_embedding(topic)

        # Find closest match in DB
        similar_posts = await post_repository.find_similar_by_embedding(
            db_session=db_session,
            embedding=embedding,
            threshold=threshold,
            limit=1,
        )

        if similar_posts:
            matched_post, score = similar_posts[0]
            logger.warning(
                "semantic_duplicate_found",
                topic=topic,
                matched_topic=matched_post.topic,
                score=score,
            )
            return matched_post.topic

        logger.info("topic_is_semantically_unique", topic=topic)
        return None


memory_service = MemoryService()
