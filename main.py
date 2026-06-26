"""
Main FastAPI application entrypoint.

Uses lifespan context manager (FastAPI modern pattern)
instead of the deprecated @app.on_event("startup").

Why lifespan?
-------------
- Cleaner startup/shutdown lifecycle management
- Officially recommended since FastAPI 0.93+
- Enables proper async resource cleanup on shutdown
"""

from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import v1_router
from app.core.config import settings
from app.core.logger import configure_logger
from app.db.init_db import init_db
from app.middleware.tracing_middleware import TracingMiddleware
from app.schedulers.post_scheduler import start_scheduler


configure_logger()


@asynccontextmanager
async def lifespan(
    app: FastAPI,
) -> AsyncGenerator[None, None]:
    """
    Application lifespan handler.

    Startup:
        - Initialize database tables
        - Start autonomous post scheduler

    Shutdown:
        - Graceful cleanup (future: close DB pool, stop scheduler)
    """

    # --- Startup ---
    await init_db()
    start_scheduler()

    yield  # Application runs here

    # --- Shutdown ---
    # Future: await engine.dispose(), scheduler.shutdown()


app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "Production-grade LinkedIn AI agent backend. "
        "Generates, schedules, and publishes LinkedIn posts "
        "using an autonomous multi-agent LangGraph pipeline."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# Register CORS middleware for frontend dev servers
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom middleware for distributed logging & tracing
app.add_middleware(TracingMiddleware)

app.include_router(
    v1_router,
)


@app.get(
    "/health",
    tags=["Infrastructure"],
    summary="Health Check",
)
async def health_check() -> dict[str, str]:
    """
    Health check endpoint.

    Returns application status. Future: add DB + Redis checks.
    """

    return {"status": "healthy", "version": "1.0.0"}