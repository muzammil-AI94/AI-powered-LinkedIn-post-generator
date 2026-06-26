"""
Centralized logging configuration.

Why this exists:
----------------
Production AI systems require structured logging for:

- debugging
- observability
- latency monitoring
- tracing failures
- monitoring workflows

This module creates a reusable structured logger
for the entire application.
"""

import logging
import sys

import structlog


def configure_logger() -> None:
    """
    Configures structured logging for the application.

    Why structured logging?
    ------------------------
    Structured logs are:
    - searchable
    - machine-readable
    - production-friendly
    - compatible with monitoring systems

    This becomes critical in distributed AI systems.
    """

    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=logging.INFO,
    )

    structlog.configure(
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            structlog.processors.JSONRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(
            logging.INFO
        ),
        logger_factory=structlog.PrintLoggerFactory(),
    )


logger = structlog.get_logger()