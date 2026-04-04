"""GET /level — return current A1 module progress."""

import logging

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session
from src.heartbeat.curriculum import get_module_progress
from src.storage.repository import Repository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/level")
async def get_level(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Return the user's current A1 module and progress."""
    repo = Repository(session)
    vocab_count = await repo.count_vocabulary()
    return get_module_progress(vocab_count)
