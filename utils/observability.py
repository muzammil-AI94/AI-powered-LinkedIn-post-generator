"""
Observability utilities for workflow tracing.

Why this module exists:
------------------------
Production AI systems need structured execution tracking:
- unique execution IDs per workflow run
- timing instrumentation per step
- structured log correlation

Why asynccontextmanager?
------------------------
The original implementation used a sync contextmanager,
but it was used inside async functions. This caused a
subtle bug where async code inside the `with` block
would not yield properly in an async context.

asynccontextmanager is the correct pattern for async code.
"""

import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from app.core.logger import logger


def generate_execution_id() -> str:
    """
    Generate unique workflow execution ID.

    Returns:
        Unique UUID string for correlating log events.
    """

    return str(uuid.uuid4())


@asynccontextmanager
async def track_workflow_execution(
    workflow_name: str,
    execution_id: str,
) -> AsyncGenerator[None, None]:
    """
    Async context manager to track workflow execution timing.

    Logs start, end, and duration of any workflow block.
    Safe to use inside async functions and Celery async wrappers.

    Args:
        workflow_name:
            Human-readable name of the workflow.

        execution_id:
            Unique identifier for this execution run.

    Usage:
        async with track_workflow_execution("my_workflow", exec_id):
            await do_async_work()
    """

    start_time = time.perf_counter()

    logger.info(
        "workflow_execution_started",
        workflow_name=workflow_name,
        execution_id=execution_id,
    )

    try:
        yield

    finally:
        duration = time.perf_counter() - start_time

        logger.info(
            "workflow_execution_completed",
            workflow_name=workflow_name,
            execution_id=execution_id,
            duration_seconds=round(duration, 3),
        )