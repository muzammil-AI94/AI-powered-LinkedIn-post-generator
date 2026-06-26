"""
Topic Intelligence Engine service for classification, scoring, and freshness decay.

Implements decaying trend popularity math and semantic clustering filters
to select the highest quality topic ideas.
"""

from datetime import datetime, timezone
import math
from typing import List, Optional
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logger import logger
from app.repositories.post_repository import post_repository
from app.services.memory_service import memory_service


class ScoredTopic(BaseModel):
    """
    Topic idea validated with intelligence scores.
    """
    topic: str
    reason: str
    niche: str = "General"
    base_score: float = 5.0  # 1-10 rating from Topic Agent
    final_score: float = 0.0


class TopicIntelligenceService:
    """
    Coordinates classification, decay metrics, and final selection ranking of topics.
    """

    async def calculate_decayed_score(
        self,
        db_session: AsyncSession,
        candidate: ScoredTopic,
        decay_lambda: float = 0.5,
    ) -> float:
        """
        Calculate decayed topic score based on semantic similarity and time decay.

        Formula:
            Final Score = Base Score * Time Decay Factor * Similarity Rejection Factor

            Time Decay Factor = 1 / (1 + Hours Since Similar Post) ^ lambda
        """
        # Find similar posts in DB
        embedding = await memory_service.get_embedding(candidate.topic)
        similar_posts = await post_repository.find_similar_by_embedding(
            db_session=db_session,
            embedding=embedding,
            threshold=0.50,  # Catch even moderate similarities for decay calculation
            limit=1,
        )

        if not similar_posts:
            # Fully fresh topic
            candidate.final_score = candidate.base_score
            return candidate.final_score

        matched_post, similarity = similar_posts[0]

        # Calculate time since the last similar post in hours
        now = datetime.now(timezone.utc)
        created_at = matched_post.created_at
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        elapsed_hours = (now - created_at).total_seconds() / 3600.0

        # Calculate decay factor
        # If similarity is very high, decay is stronger
        time_decay = 1.0 / math.pow(1.0 + elapsed_hours, decay_lambda)
        similarity_penalty = 1.0 - (similarity * 0.8) # 80% reduction for near-duplicates

        decayed_score = candidate.base_score * time_decay * similarity_penalty
        candidate.final_score = max(0.0, round(decayed_score, 2))

        logger.info(
            "calculated_topic_decay",
            topic=candidate.topic,
            base_score=candidate.base_score,
            similarity=round(similarity, 2),
            elapsed_hours=round(elapsed_hours, 1),
            final_score=candidate.final_score,
        )
        return candidate.final_score

    async def rank_and_select_best_topic(
        self,
        db_session: AsyncSession,
        candidates: List[ScoredTopic],
    ) -> Optional[ScoredTopic]:
        """
        Score a list of candidate topics and return the highest ranked one.
        """
        if not candidates:
            return None

        # Apply decay to all candidates
        for candidate in candidates:
            await self.calculate_decayed_score(db_session, candidate)

        # Sort by final score descending
        candidates.sort(key=lambda x: x.final_score, reverse=True)

        best_topic = candidates[0]
        logger.info(
            "selected_best_topic",
            topic=best_topic.topic,
            score=best_topic.final_score,
            niche=best_topic.niche,
        )
        return best_topic


topic_intelligence_service = TopicIntelligenceService()
