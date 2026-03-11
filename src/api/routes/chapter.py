"""GET /chapter/today — fetch pre-generated daily chapter."""

import json
import logging
from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session
from src.storage.repository import Repository

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/chapter/today")
async def get_today_chapter(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get today's pre-generated chapter (from heartbeat).

    Returns the chapter if available, or a flag indicating manual generation needed.
    """
    repo = Repository(session)
    today = date.today().isoformat()

    chapter = await repo.get_daily_chapter(today)
    if chapter:
        content = json.loads(chapter.content_json)
        return {
            "available": True,
            "date": chapter.date,
            "category": chapter.category,
            "vocab_added": chapter.vocab_added,
            "sentences_added": chapter.sentences_added,
            **content,
        }

    return {
        "available": False,
        "date": today,
        "message": "今天的课程还未生成，请手动生成或等待自动生成",
    }


@router.get("/chapter/{date_str}")
async def get_chapter_by_date(
    date_str: str,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get a pre-generated chapter for a specific date."""
    repo = Repository(session)
    chapter = await repo.get_daily_chapter(date_str)
    if chapter:
        content = json.loads(chapter.content_json)
        return {
            "available": True,
            "date": chapter.date,
            "category": chapter.category,
            **content,
        }

    return {
        "available": False,
        "date": date_str,
        "message": "该日期的课程不存在",
    }
