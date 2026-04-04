"""FastAPI app factory + lifespan events."""

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.dependencies import get_config, get_db_path, init_provider_from_config, load_config
from src.api.middleware import APIKeyMiddleware, RequestLoggingMiddleware
from src.api.routes import chapter, daily_plan, grammar, health, heartbeat, learning, level, memory, provider, sentences, vocabulary
from src.storage.database import close_engine, get_engine
from src.storage.migrations import run_migrations

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Startup and shutdown logic."""
    # Startup
    load_config()
    config = get_config()

    # Configure logging
    log_level = config.get("app", {}).get("log_level", "INFO")
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    # Initialize database
    db_path = get_db_path()
    engine = get_engine(db_path)
    await run_migrations(engine)

    # Initialize AI provider
    init_provider_from_config()

    # Initialize heartbeat scheduler if enabled
    hb_config = config.get("heartbeat", {})
    if hb_config.get("enabled", False):
        try:
            from src.heartbeat.scheduler import HeartbeatScheduler

            scheduler = HeartbeatScheduler(config=hb_config, db_path=db_path)
            heartbeat.set_scheduler(scheduler)
            scheduler.start()
            logger.info("Heartbeat scheduler started")
        except Exception:
            logger.exception("Failed to start heartbeat scheduler")

    logger.info("DeutschLerner API server started")
    yield

    # Shutdown
    try:
        from src.api.routes.heartbeat import _scheduler

        if _scheduler and hasattr(_scheduler, "stop"):
            _scheduler.stop()
    except Exception:
        pass

    await close_engine()
    logger.info("DeutschLerner API server stopped")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    app = FastAPI(
        title="DeutschLerner API",
        description="German language learning assistant (Chinese → German)",
        version="1.0.0",
        lifespan=lifespan,
    )

    # Middleware (order matters — last added = first executed)
    app.add_middleware(RequestLoggingMiddleware)
    app.add_middleware(APIKeyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    prefix = "/api/v1"
    app.include_router(health.router, prefix=prefix, tags=["System"])
    app.include_router(chapter.router, prefix=prefix, tags=["Chapter"])
    app.include_router(daily_plan.router, prefix=prefix, tags=["Daily Plan"])
    app.include_router(learning.router, prefix=prefix, tags=["Learning"])
    app.include_router(vocabulary.router, prefix=prefix, tags=["Vocabulary"])
    app.include_router(sentences.router, prefix=prefix, tags=["Sentences"])
    app.include_router(memory.router, prefix=prefix, tags=["Memory"])
    app.include_router(heartbeat.router, prefix=prefix, tags=["Heartbeat"])
    app.include_router(grammar.router, prefix=prefix, tags=["Grammar"])
    app.include_router(level.router, prefix=prefix, tags=["Level"])
    app.include_router(provider.router, prefix=prefix, tags=["Provider"])

    return app
