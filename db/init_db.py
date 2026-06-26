"""
Database initialization utilities.
"""

from sqlalchemy import text
from app.core.config import settings
from app.db.database import Base, engine
from app.db.models.post_model import GeneratedPost


async def init_db() -> None:
    """
    Initialize database tables and register extensions.
    """

    async with engine.begin() as connection:
        if not settings.DATABASE_URL.startswith("sqlite"):
            # Enable pgvector extension inside Postgres
            await connection.execute(
                text("CREATE EXTENSION IF NOT EXISTS vector;")
            )

        await connection.run_sync(
            Base.metadata.create_all
        )