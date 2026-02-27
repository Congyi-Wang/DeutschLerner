"""Test LearningEngine logic."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.engine import LearningEngine
from src.core.marker import Marker
from src.core.memory import MemoryManager
from src.storage.repository import Repository
from tests.conftest import MockProvider


@pytest.mark.asyncio
async def test_learn_topic(db_session: AsyncSession, mock_provider: MockProvider) -> None:
    repo = Repository(db_session)
    memory = MemoryManager(repo)
    marker = Marker(repo)
    engine = LearningEngine(mock_provider, memory, marker, repo)

    result = await engine.learn_topic("在超市购物")

    assert result.topic.topic_title_de == "Im Supermarkt einkaufen"
    assert result.topic.topic_title_cn == "在超市购物"
    assert result.vocab_added == 3
    assert result.sentences_added == 2
    assert result.duration_seconds >= 0


@pytest.mark.asyncio
async def test_learn_topic_dedup(db_session: AsyncSession, mock_provider: MockProvider) -> None:
    """Second call with same data should not add duplicate vocabulary."""
    repo = Repository(db_session)
    memory = MemoryManager(repo)
    marker = Marker(repo)
    engine = LearningEngine(mock_provider, memory, marker, repo)

    result1 = await engine.learn_topic("购物")
    result2 = await engine.learn_topic("购物")

    assert result1.vocab_added == 3
    assert result2.vocab_added == 0  # All duplicates


@pytest.mark.asyncio
async def test_review_vocabulary(db_session: AsyncSession, mock_provider: MockProvider) -> None:
    repo = Repository(db_session)
    memory = MemoryManager(repo)
    marker = Marker(repo)
    engine = LearningEngine(mock_provider, memory, marker, repo)

    # Generate some vocab first
    await engine.learn_topic("购物")
    items = await engine.review_vocabulary(10)

    assert len(items) == 3
    assert items[0]["status"] == "unknown"


@pytest.mark.asyncio
async def test_mark_item(db_session: AsyncSession, mock_provider: MockProvider) -> None:
    repo = Repository(db_session)
    memory = MemoryManager(repo)
    marker = Marker(repo)
    engine = LearningEngine(mock_provider, memory, marker, repo)

    await engine.learn_topic("购物")
    items = await engine.review_vocabulary(10)
    vocab_id = items[0]["id"]

    success = await engine.mark_item("vocabulary", vocab_id, "known")
    assert success is True

    # Verify status changed
    item = await repo.get_vocabulary(vocab_id)
    assert item is not None
    assert item.status == "known"
    assert item.review_count == 1
