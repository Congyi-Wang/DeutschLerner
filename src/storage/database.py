"""SQLite async database connection manager."""

import logging
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

logger = logging.getLogger(__name__)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def get_engine(db_path: str = "data/deutsch_lerner.db") -> AsyncEngine:
    """Get or create the async SQLite engine."""
    global _engine
    if _engine is None:
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        url = f"sqlite+aiosqlite:///{db_path}"
        _engine = create_async_engine(url, echo=False)
        logger.info("Database engine created: %s", db_path)
    return _engine


def get_session_factory(db_path: str = "data/deutsch_lerner.db") -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _session_factory
    if _session_factory is None:
        engine = get_engine(db_path)
        _session_factory = async_sessionmaker(engine, expire_on_commit=False)
    return _session_factory


async def get_session(db_path: str = "data/deutsch_lerner.db") -> AsyncSession:
    """Create a new async session."""
    factory = get_session_factory(db_path)
    return factory()


async def close_engine() -> None:
    """Dispose of the engine and reset global state."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine closed")
