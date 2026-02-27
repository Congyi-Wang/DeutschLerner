"""Dependency injection for FastAPI — DB session, AI provider, etc."""

import logging
import os
from typing import AsyncIterator

import yaml
from sqlalchemy.ext.asyncio import AsyncSession

from src.ai.base import AIProvider
from src.ai.factory import create_provider
from src.core.engine import LearningEngine
from src.core.marker import Marker
from src.core.memory import MemoryManager
from src.storage.database import get_session_factory
from src.storage.repository import Repository

logger = logging.getLogger(__name__)

_config: dict | None = None
_current_provider_name: str = "claude"
_current_model: str | None = None


def load_config(path: str = "config.yaml") -> dict:
    """Load configuration from YAML file."""
    global _config
    if _config is None:
        try:
            with open(path, encoding="utf-8") as f:
                _config = yaml.safe_load(f)
        except FileNotFoundError:
            logger.warning("Config file not found at %s, using defaults", path)
            _config = {}
    return _config


def get_config() -> dict:
    """Get the loaded configuration."""
    if _config is None:
        return load_config()
    return _config


def get_db_path() -> str:
    """Get the database path from config."""
    config = get_config()
    return config.get("database", {}).get("path", "data/deutsch_lerner.db")


async def get_db_session() -> AsyncIterator[AsyncSession]:
    """Yield an async database session."""
    factory = get_session_factory(get_db_path())
    session = factory()
    try:
        yield session
    finally:
        await session.close()


async def get_repository(session: AsyncSession) -> Repository:
    """Create a Repository from a session."""
    return Repository(session)


def get_ai_provider() -> AIProvider:
    """Get the current AI provider."""
    return create_provider(_current_provider_name, _current_model)


def set_ai_provider(name: str, model: str | None = None) -> AIProvider:
    """Switch the current AI provider."""
    global _current_provider_name, _current_model
    provider = create_provider(name, model)
    _current_provider_name = name
    _current_model = model
    logger.info("AI provider switched to: %s (model: %s)", name, model)
    return provider


def get_current_provider_info() -> dict:
    """Get info about the current provider."""
    return {
        "provider": _current_provider_name,
        "model": _current_model,
    }


async def get_engine(session: AsyncSession) -> LearningEngine:
    """Build a fully-wired LearningEngine."""
    repo = Repository(session)
    memory = MemoryManager(repo)
    marker = Marker(repo)
    provider = get_ai_provider()
    return LearningEngine(provider, memory, marker, repo)


def init_provider_from_config() -> None:
    """Initialize the AI provider from config on startup."""
    global _current_provider_name, _current_model
    config = get_config()
    ai_config = config.get("ai", {})
    _current_provider_name = ai_config.get("default_provider", "claude")
    _current_model = ai_config.get("default_model")
    logger.info("Default AI provider: %s", _current_provider_name)
