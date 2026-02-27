"""GET /memory/export, POST /memory/import — data portability."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session
from src.core.memory import MemoryManager
from src.storage.repository import Repository

router = APIRouter()


class ImportRequest(BaseModel):
    """Request body for data import."""

    vocabulary: list[dict] = []
    sentences: list[dict] = []


@router.get("/memory/export")
async def export_memory(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Export all learning data as JSON."""
    repo = Repository(session)
    memory = MemoryManager(repo)
    return await memory.export_data()


@router.post("/memory/import")
async def import_memory(
    body: ImportRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Import learning data from JSON."""
    repo = Repository(session)
    memory = MemoryManager(repo)
    counts = await memory.import_data(body.model_dump())
    return {"imported": counts}


@router.get("/memory/stats")
async def memory_stats(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get overall learning statistics."""
    repo = Repository(session)
    memory = MemoryManager(repo)
    return await memory.get_stats()
