"""
Embedding utilities for semantic similarity.
"""

from typing import List

import numpy as np

from app.core.config import settings
from app.core.logger import logger
from app.services.openai_service import (
    openai_service,
)


class EmbeddingService:
    """
    Semantic embedding utilities.
    """

    async def generate_embedding(
        self,
        text: str,
    ) -> List[float]:
        """
        Generate semantic embedding vector.

        Args:
            text:
                Input text.

        Returns:
            Embedding vector.
        """

        logger.info(
            "embedding_generation_started",
        )

        response = (
            await openai_service.client.embeddings.create(
                model="text-embedding-3-small",
                input=text,
            )
        )

        embedding = (
            response.data[0].embedding
        )

        logger.info(
            "embedding_generation_completed",
        )

        return embedding

    def cosine_similarity(
        self,
        embedding_1: List[float],
        embedding_2: List[float],
    ) -> float:
        """
        Calculate cosine similarity.

        Args:
            embedding_1:
                First embedding vector.

            embedding_2:
                Second embedding vector.

        Returns:
            Semantic similarity score.
        """

        vector_1 = np.array(
            embedding_1,
        )

        vector_2 = np.array(
            embedding_2,
        )

        similarity = np.dot(
            vector_1,
            vector_2,
        ) / (
            np.linalg.norm(vector_1)
            * np.linalg.norm(vector_2)
        )

        return float(
            similarity,
        )


embedding_service = EmbeddingService()