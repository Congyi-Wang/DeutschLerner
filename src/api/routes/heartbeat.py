"""Heartbeat control: start/stop/status/trigger."""

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session
from src.storage.repository import Repository

router = APIRouter()

# The scheduler reference is set by the server lifespan
_scheduler = None


def set_scheduler(scheduler: object) -> None:
    """Set the scheduler reference (called from server.py)."""
    global _scheduler
    _scheduler = scheduler


@router.get("/heartbeat/status")
async def heartbeat_status() -> dict:
    """Get current heartbeat scheduler status."""
    if _scheduler is None:
        return {"status": "not_initialized"}
    running = getattr(_scheduler, "running", False)
    return {"status": "running" if running else "stopped"}


@router.post("/heartbeat/start")
async def heartbeat_start() -> dict:
    """Start the heartbeat scheduler."""
    if _scheduler is None:
        return {"error": "Scheduler not initialized"}
    if hasattr(_scheduler, "start"):
        _scheduler.start()
    return {"status": "started"}


@router.post("/heartbeat/stop")
async def heartbeat_stop() -> dict:
    """Stop the heartbeat scheduler."""
    if _scheduler is None:
        return {"error": "Scheduler not initialized"}
    if hasattr(_scheduler, "stop"):
        _scheduler.stop()
    return {"status": "stopped"}


@router.post("/heartbeat/trigger")
async def heartbeat_trigger(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Manually trigger one heartbeat cycle."""
    if _scheduler is None:
        return {"error": "Scheduler not initialized"}
    if hasattr(_scheduler, "trigger_now"):
        result = await _scheduler.trigger_now()
        return {"status": "triggered", "result": result}
    return {"error": "Scheduler does not support manual trigger"}


@router.get("/heartbeat/history")
async def heartbeat_history(
    limit: int = 50,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """View past heartbeat topics."""
    repo = Repository(session)
    topics = await repo.list_topic_history(limit=limit)
    return {
        "items": [
            {
                "id": t.id,
                "topic": t.topic,
                "category": t.category,
                "source": t.source,
                "sent_via": t.sent_via,
                "created_at": t.created_at.isoformat() if t.created_at else None,
            }
            for t in topics
        ],
    }
