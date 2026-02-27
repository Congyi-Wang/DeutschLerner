"""CRUD /sentences — manage sentences."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session
from src.core.marker import Marker
from src.storage.repository import Repository

router = APIRouter()


class SentenceCreate(BaseModel):
    """Request body for creating a sentence."""

    german: str
    chinese: str
    grammar_notes: str | None = None
    source_topic: str | None = None


class SentenceUpdate(BaseModel):
    """Request body for updating a sentence."""

    status: str | None = None
    chinese: str | None = None
    grammar_notes: str | None = None


@router.get("/sentences")
async def list_sentences(
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """List all sentences with optional status filter."""
    repo = Repository(session)
    items = await repo.list_sentences(status=status, limit=limit, offset=offset)
    total = await repo.count_sentences(status=status)
    return {
        "items": [
            {
                "id": s.id,
                "german": s.german,
                "chinese": s.chinese,
                "grammar_notes": s.grammar_notes,
                "source_topic": s.source_topic,
                "status": s.status,
                "review_count": s.review_count,
                "created_at": s.created_at.isoformat() if s.created_at else None,
            }
            for s in items
        ],
        "total": total,
    }


@router.post("/sentences", status_code=201)
async def create_sentence(
    body: SentenceCreate,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Add a new sentence manually."""
    repo = Repository(session)
    item = await repo.add_sentence(**body.model_dump())
    await repo.commit()
    return {"id": item.id, "german": item.german, "status": item.status}


@router.patch("/sentences/{sentence_id}")
async def update_sentence(
    sentence_id: int,
    body: SentenceUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Update a sentence (e.g. mark as known/unknown)."""
    repo = Repository(session)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}

    if "status" in updates:
        marker = Marker(repo)
        success = await marker.mark_sentence(sentence_id, updates.pop("status"))
        if not success:
            raise HTTPException(status_code=404, detail="Sentence not found")

    if updates:
        item = await repo.update_sentence(sentence_id, **updates)
        if item is None:
            raise HTTPException(status_code=404, detail="Sentence not found")

    await repo.commit()
    return {"id": sentence_id, "updated": True}
