"""
Stateless API Request Tracing and Latency Monitoring Middleware.

Generates a correlation/execution ID for every incoming HTTP request and binds it
to the execution context for tracing backend logs and workflow actions.
"""

import time
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logger import logger
from app.utils.observability import generate_execution_id


class TracingMiddleware(BaseHTTPMiddleware):
    """
    HTTP Middleware tracking latency and correlation IDs for request lifecycle.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: Callable,
    ) -> Response:
        # Check if client passed correlation ID, otherwise generate one
        execution_id = request.headers.get("X-Execution-ID") or generate_execution_id()

        # Bind context details for execution lifecycle
        request.state.execution_id = execution_id

        start_time = time.perf_counter()

        logger.info(
            "http_request_started",
            method=request.method,
            path=request.url.path,
            execution_id=execution_id,
        )

        try:
            response = await call_next(request)
        except Exception as err:
            duration = time.perf_counter() - start_time
            logger.error(
                "http_request_failed",
                method=request.method,
                path=request.url.path,
                execution_id=execution_id,
                duration_seconds=round(duration, 3),
                error=str(err),
            )
            # Add tracing headers to response
            response = Response(content="Internal Server Error", status_code=500)
            response.headers["X-Execution-ID"] = execution_id
            return response

        duration = time.perf_counter() - start_time

        logger.info(
            "http_request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            execution_id=execution_id,
            duration_seconds=round(duration, 3),
        )

        # Inject tracing correlation ID header into response
        response.headers["X-Execution-ID"] = execution_id
        response.headers["X-Process-Time"] = f"{round(duration * 1000, 2)}ms"

        return response
