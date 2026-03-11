"""POST /learn — generate topic from user input."""

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session, get_engine

router = APIRouter()


class LearnRequest(BaseModel):
    """Request body for topic generation."""

    input: str
    provider: str | None = None


class LearnResponse(BaseModel):
    """Response body for generated topic."""

    topic_title_de: str
    topic_title_cn: str
    summary_cn: str
    vocabulary: list[dict]
    sentences: list[dict]
    grammar_tips: str
    grammar_analysis: dict | None = None
    exercise: str
    vocab_added: int
    sentences_added: int
    duration_seconds: int


class ReviewRequest(BaseModel):
    """Request body for vocabulary review."""

    count: int = 10


@router.post("/learn", response_model=LearnResponse)
async def learn_topic(
    body: LearnRequest,
    session: AsyncSession = Depends(get_db_session),
) -> LearnResponse:
    """Generate a learning topic from user input."""
    engine = await get_engine(session)
    result = await engine.learn_topic(body.input)
    return LearnResponse(
        topic_title_de=result.topic.topic_title_de,
        topic_title_cn=result.topic.topic_title_cn,
        summary_cn=result.topic.summary_cn,
        vocabulary=result.topic.vocabulary,
        sentences=result.topic.sentences,
        grammar_tips=result.topic.grammar_tips,
        grammar_analysis=result.topic.grammar_analysis,
        exercise=result.topic.exercise,
        vocab_added=result.vocab_added,
        sentences_added=result.sentences_added,
        duration_seconds=result.duration_seconds,
    )


@router.post("/learn/review")
async def review_vocabulary(
    body: ReviewRequest,
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Get vocabulary items for review."""
    engine = await get_engine(session)
    items = await engine.review_vocabulary(body.count)
    return {"items": items, "count": len(items)}
