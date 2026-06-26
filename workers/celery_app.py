"""
Celery application configuration.

Configures connection settings, queues, and task routing schemas
including support for Dead-Letter Queues (DLQ).
"""

from celery import Celery
from kombu import Exchange, Queue

from app.core.config import settings


celery_app = Celery(
    "linkedin_ai_agent",
)

# Redis Broker & Result Backend
celery_app.conf.broker_url = settings.CELERY_BROKER_URL
celery_app.conf.result_backend = settings.CELERY_RESULT_BACKEND

# Explicit Task Imports
celery_app.conf.imports = (
    "app.workers.workflow_tasks",
)

# Queue Topology Definitions
default_exchange = Exchange("linkedin_workflow", type="direct")
dlq_exchange = Exchange(settings.CELERY_DLQ_NAME, type="direct")

celery_app.conf.task_queues = (
    Queue(
        "linkedin_workflow",
        exchange=default_exchange,
        routing_key="linkedin_workflow",
    ),
    Queue(
        settings.CELERY_DLQ_NAME,
        exchange=dlq_exchange,
        routing_key=settings.CELERY_DLQ_NAME,
    ),
)

# Routing defaults
celery_app.conf.task_default_queue = "linkedin_workflow"
celery_app.conf.task_default_exchange = "linkedin_workflow"
celery_app.conf.task_default_routing_key = "linkedin_workflow"

# Safety settings: limit task execution times
celery_app.conf.task_time_limit = 900  # 15 minutes max
celery_app.conf.task_soft_time_limit = 600  # 10 minutes warning