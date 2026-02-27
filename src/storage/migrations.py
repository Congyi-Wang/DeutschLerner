"""Auto-migration: create all tables on startup."""

import logging

from sqlalchemy.ext.asyncio import AsyncEngine

from src.storage.models import Base

logger = logging.getLogger(__name__)


async def run_migrations(engine: AsyncEngine) -> None:
    """Create all tables if they don't exist."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database migrations complete — all tables ensured")
