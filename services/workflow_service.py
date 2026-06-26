"""
Autonomous workflow service for synchronous (non-worker) execution.

Used for debugging and synchronous execution paths.
"""

from app.core.logger import logger
from app.db.database import AsyncSessionLocal
from app.graphs.linkedin_graph import linkedin_graph
from app.repositories.post_repository import post_repository
from app.services.memory_service import memory_service


async def run_autonomous_workflow() -> None:
    """
    Execute autonomous LinkedIn workflow synchronously and persist results.
    """

    logger.info("sync_workflow_started")

    try:
        result = await linkedin_graph.ainvoke({})

        topic = result.get("topic")
        final_post = result.get("final_post")

        if not topic or not final_post:
            raise ValueError("Workflow output missing required topic or post content.")

        async with AsyncSessionLocal() as session:
            # Check for duplicate
            duplicate = await memory_service.check_semantic_duplicate(
                db_session=session,
                topic=topic,
                threshold=0.85,
            )

            if duplicate:
                logger.warning(
                    "sync_workflow_duplicate_detected",
                    topic=topic,
                )
                return

            # Get embedding
            embedding = await memory_service.get_embedding(topic)

            # Persist
            post_in = {
                "topic": topic,
                "topic_reason": result.get("topic_reason", ""),
                "post_content": final_post,
                "niche": result.get("niche", "General"),
                "engagement_score": result.get("final_score", 0.0),
                "embedding": embedding,
            }

            await post_repository.create(
                db_session=session,
                obj_in=post_in,
            )

        logger.info(
            "sync_workflow_completed",
            topic=topic,
        )

    except Exception as error:
        logger.error(
            "sync_workflow_failed",
            error=str(error),
        )