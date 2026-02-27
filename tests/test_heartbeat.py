"""Test scheduler + topic selection + dedup."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.heartbeat.topic_selector import TopicSelector, TOPIC_CATEGORIES
from src.storage.repository import Repository


@pytest.mark.asyncio
async def test_select_category(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    selector = TopicSelector(repo)

    category = await selector.select_category()
    assert category in TOPIC_CATEGORIES


@pytest.mark.asyncio
async def test_category_weighting(db_session: AsyncSession) -> None:
    """Less-used categories should be weighted higher."""
    repo = Repository(db_session)
    selector = TopicSelector(repo)

    # Record many topics in one category
    for _ in range(10):
        await repo.add_topic_history(
            topic=f"topic_{_}",
            category="grammar",
            content="content",
            source="heartbeat",
        )
    await repo.commit()

    # Run many selections — grammar should appear less often
    categories = []
    for _ in range(50):
        cat = await selector.select_category()
        categories.append(cat)

    grammar_count = categories.count("grammar")
    # Grammar should be picked less often due to weighting
    assert grammar_count < 40  # Generous bound


@pytest.mark.asyncio
async def test_duplicate_check(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    selector = TopicSelector(repo)

    assert await selector.is_duplicate("New Topic") is False

    await selector.record_topic(
        topic="New Topic",
        category="daily_life",
        content="some content",
        sent_via="discord",
    )

    assert await selector.is_duplicate("New Topic") is True
    assert await selector.is_duplicate("Another Topic") is False
