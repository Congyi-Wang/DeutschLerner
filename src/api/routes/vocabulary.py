"""CRUD /vocabulary — manage vocabulary items."""

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session
from src.core.marker import Marker
from src.storage.repository import Repository

router = APIRouter()


class VocabularyCreate(BaseModel):
    """Request body for creating a vocabulary item."""

    german: str
    chinese: str
    phonetic: str | None = None
    part_of_speech: str | None = None
    gender: str | None = None
    example: str | None = None
    difficulty: int = 0


class VocabularyUpdate(BaseModel):
    """Request body for updating a vocabulary item."""

    status: str | None = None
    chinese: str | None = None
    phonetic: str | None = None
    part_of_speech: str | None = None
    gender: str | None = None
    example: str | None = None
    difficulty: int | None = None


@router.get("/vocabulary")
async def list_vocabulary(
    status: str | None = None,
    limit: int = 100,
    offset: int = 0,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """List all vocabulary items with optional status filter."""
    repo = Repository(session)
    items = await repo.list_vocabulary(status=status, limit=limit, offset=offset)
    total = await repo.count_vocabulary(status=status)
    return {
        "items": [
            {
                "id": v.id,
                "german": v.german,
                "chinese": v.chinese,
                "phonetic": v.phonetic,
                "part_of_speech": v.part_of_speech,
                "gender": v.gender,
                "example": v.example,
                "status": v.status,
                "difficulty": v.difficulty,
                "review_count": v.review_count,
                "created_at": v.created_at.isoformat() if v.created_at else None,
            }
            for v in items
        ],
        "total": total,
    }


@router.post("/vocabulary", status_code=201)
async def create_vocabulary(
    body: VocabularyCreate,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Add a new vocabulary item manually."""
    repo = Repository(session)
    item = await repo.add_vocabulary(**body.model_dump())
    await repo.commit()
    return {"id": item.id, "german": item.german, "status": item.status}


@router.patch("/vocabulary/{vocab_id}")
async def update_vocabulary(
    vocab_id: int,
    body: VocabularyUpdate,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Update a vocabulary item (e.g. mark as known/unknown)."""
    repo = Repository(session)
    updates = {k: v for k, v in body.model_dump().items() if v is not None}

    if "status" in updates:
        marker = Marker(repo)
        success = await marker.mark_vocabulary(vocab_id, updates.pop("status"))
        if not success:
            raise HTTPException(status_code=404, detail="Vocabulary not found")

    if updates:
        item = await repo.update_vocabulary(vocab_id, **updates)
        if item is None:
            raise HTTPException(status_code=404, detail="Vocabulary not found")

    await repo.commit()
    return {"id": vocab_id, "updated": True}


@router.delete("/vocabulary/{vocab_id}")
async def delete_vocabulary(
    vocab_id: int,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Remove a vocabulary item."""
    repo = Repository(session)
    deleted = await repo.delete_vocabulary(vocab_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Vocabulary not found")
    await repo.commit()
    return {"id": vocab_id, "deleted": True}


@router.get("/vocabulary/stats")
async def vocabulary_stats(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get vocabulary statistics."""
    repo = Repository(session)
    return {
        "total": await repo.count_vocabulary(),
        "known": await repo.count_vocabulary("known"),
        "learning": await repo.count_vocabulary("learning"),
        "unknown": await repo.count_vocabulary("unknown"),
    }
