"""
Distributed autonomous workflow tasks.

Orchestrates multi-agent execution, runs semantic vector checks,
handles database persistence, and manages error recovery retries.
"""

import asyncio
from typing import Dict, Any, Optional

from app.core.logger import logger
from app.db.database import AsyncSessionLocal
from app.graphs.linkedin_graph import linkedin_graph, update_task_stage
from app.publishers.linkedin_publisher import linkedin_publisher
from app.repositories.post_repository import post_repository
from app.services.memory_service import memory_service
from app.agents.image_agent import image_prompt_agent
from app.services.openai_service import openai_service
from app.utils.observability import (
    generate_execution_id,
    track_workflow_execution,
)
from app.workers.celery_app import celery_app
from app.utils.cache import cache


class WorkflowTaskFailureHandler:
    """
    Handles logging and routing for persistent task failures.
    """

    def handle_failure(self, task, exc, task_id, args, kwargs, einfo):
        logger.critical(
            "workflow_task_permanently_failed",
            task_name=task.name,
            task_id=task_id,
            error=str(exc),
            detail="Routing to Dead Letter Queue (DLQ).",
        )
        # Update stage to error so frontend stops polling
        update_task_stage(task_id, "FAILED")


@celery_app.task(
    bind=True,
    name="app.workers.workflow_tasks.execute_linkedin_workflow",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
    on_failure=WorkflowTaskFailureHandler().handle_failure,
)
def execute_linkedin_workflow(
    self,
    topic: Optional[str] = None,
    audience: Optional[str] = "professionals",
    tone: Optional[str] = "professional",
    generate_image: Optional[bool] = False,
) -> Dict[str, Any]:
    """
    Celery task wrapping the async workflow execution.
    """
    task_id = self.request.id
    return asyncio.run(
        _execute_workflow(
            task_id=task_id,
            topic=topic,
            audience=audience,
            tone=tone,
            generate_image=generate_image,
        )
    )


async def _execute_workflow(
    task_id: str,
    topic: Optional[str],
    audience: Optional[str],
    tone: Optional[str],
    generate_image: Optional[bool],
) -> Dict[str, Any]:
    """
    Internal asynchronous runner executing the LinkedIn pipeline.
    """
    execution_id = generate_execution_id()

    # Track stage
    update_task_stage(task_id, "TOPIC_DISCOVERY")

    async with track_workflow_execution(
        workflow_name="linkedin_autonomous_workflow",
        execution_id=execution_id,
    ):
        logger.info(
            "distributed_workflow_started",
            execution_id=execution_id,
            task_id=task_id,
        )

        # 1. Run the LangGraph orchestration with passed variables
        initial_state = {
            "topic": topic,
            "audience": audience,
            "tone": tone,
            "generate_image": generate_image,
            "task_id": task_id,
        }

        result = await linkedin_graph.ainvoke(initial_state)

        resolved_topic = result.get("topic")
        final_post = result.get("final_post")

        if not resolved_topic or not final_post:
            raise ValueError("Workflow output missing required topic or post content.")

        async with AsyncSessionLocal() as session:
            # 2. Final double check for semantic duplicates
            duplicate = await memory_service.check_semantic_duplicate(
                db_session=session,
                topic=resolved_topic,
                threshold=0.85,
            )

            if duplicate:
                logger.warning(
                    "duplicate_prevention_triggered",
                    topic=resolved_topic,
                    matched_duplicate=duplicate,
                )
                update_task_stage(task_id, "COMPLETED")
                return {"status": "skipped", "reason": "semantic duplicate"}

            # 3. Generate embedding vector for the selected topic
            embedding = await memory_service.get_embedding(resolved_topic)

            # 4. Persist to DB using repository pattern
            post_in = {
                "topic": resolved_topic,
                "topic_reason": result.get("topic_reason", ""),
                "post_content": final_post,
                "niche": result.get("niche", "General"),
                "engagement_score": result.get("final_score", 0.0),
                "embedding": embedding,
            }

            db_post = await post_repository.create(
                db_session=session,
                obj_in=post_in,
            )

            logger.info(
                "generated_post_saved",
                post_id=db_post.id,
                topic=resolved_topic,
            )

            # 5. Non-blocking Async Image Generation (if enabled)
            if generate_image:
                logger.info(
                    "triggering_background_image_generation",
                    post_id=db_post.id,
                    task_id=task_id,
                )
                generate_post_image_task.delay(
                    post_id=db_post.id,
                    post_content=final_post,
                    task_id=task_id,
                )
            else:
                # If no image is needed, the task is fully complete now
                update_task_stage(task_id, "COMPLETED")

            # 6. Publish to LinkedIn
            published = await linkedin_publisher.publish_post(final_post)
            if not published:
                raise RuntimeError("Failed to publish generated post to LinkedIn.")

        logger.info(
            "distributed_workflow_completed",
            execution_id=execution_id,
        )

        return {
            "status": "success",
            "post_id": db_post.id,
            "topic": resolved_topic,
        }


@celery_app.task(
    bind=True,
    name="app.workers.workflow_tasks.generate_post_image_task",
    autoretry_for=(Exception,),
    retry_backoff=True,
    retry_kwargs={"max_retries": 3},
)
def generate_post_image_task(
    self,
    post_id: int,
    post_content: str,
    task_id: str,
) -> str:
    """
    Asynchronous, non-blocking Celery task to generate visuals for LinkedIn posts.
    """
    return asyncio.run(
        _execute_image_generation(
            post_id=post_id,
            post_content=post_content,
            task_id=task_id,
        )
    )


async def _execute_image_generation(
    post_id: int,
    post_content: str,
    task_id: str,
) -> str:
    """
    Internal runner to generate an image prompt, invoke DALL-E, and update the database.
    """
    logger.info("background_image_generation_task_started", post_id=post_id)

    # 1. Update task stage to IMAGE_GENERATION in cache
    update_task_stage(task_id, "IMAGE_GENERATION")

    try:
        # 2. Generate visually compelling prompt using ImagePromptAgent
        prompt = await image_prompt_agent.run(post_content)

        # 3. Call DALL-E 3 image generation
        image_url = await openai_service.generate_image(prompt)

        # 4. Save the generated image details to DB
        async with AsyncSessionLocal() as session:
            post = await post_repository.get(session, post_id)
            if post:
                post.image_url = image_url
                post.image_prompt = prompt
                await session.commit()
                logger.info(
                    "background_image_generation_completed",
                    post_id=post_id,
                    image_url=image_url,
                )

        # 5. Finalize progress to COMPLETED
        update_task_stage(task_id, "COMPLETED")
        return image_url

    except Exception as err:
        logger.error(
            "background_image_generation_failed",
            post_id=post_id,
            error=str(err),
        )
        # Ensure stage marks as COMPLETED so frontend terminates spinner, even if image fails
        update_task_stage(task_id, "COMPLETED")
        raise err