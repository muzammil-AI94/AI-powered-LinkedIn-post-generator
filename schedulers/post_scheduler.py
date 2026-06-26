"""
Autonomous workflow scheduler.

Responsibilities:
-----------------
- schedule recurring workflow execution
- enqueue distributed AI jobs
- trigger autonomous execution
"""

from apscheduler.schedulers.asyncio import (
    AsyncIOScheduler,
)

from app.core.logger import logger
from app.workers.workflow_tasks import (
    execute_linkedin_workflow,
)

scheduler = AsyncIOScheduler()


async def run_autonomous_workflow() -> None:
    """
    Queue autonomous LinkedIn workflow.
    """

    logger.info(
        "scheduling_distributed_workflow",
    )

    try:

        # Queue distributed task
        execute_linkedin_workflow.delay()

        logger.info(
            "workflow_queued_successfully",
        )

    except Exception as error:

        logger.error(
            "workflow_queue_failed",
            error=str(error),
        )


def start_scheduler() -> None:
    """
    Start recurring scheduler.
    """

    scheduler.add_job(
        run_autonomous_workflow,
        trigger="interval",
        days=1,
    )

    scheduler.start()

    logger.info(
        "scheduler_started",
    )