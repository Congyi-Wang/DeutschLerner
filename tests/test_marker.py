"""Test mark/unmark operations."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.marker import Marker
from src.storage.repository import Repository


@pytest.mark.asyncio
async def test_mark_vocabulary_known(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    marker = Marker(repo)

    vocab = await repo.add_vocabulary(german="Haus", chinese="房子")
    await repo.commit()

    success = await marker.mark_vocabulary(vocab.id, "known")
    assert success is True

    updated = await repo.get_vocabulary(vocab.id)
    assert updated is not None
    assert updated.status == "known"
    assert updated.review_count == 1
    assert updated.last_reviewed_at is not None


@pytest.mark.asyncio
async def test_mark_vocabulary_invalid_status(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    marker = Marker(repo)

    vocab = await repo.add_vocabulary(german="Haus", chinese="房子")
    await repo.commit()

    with pytest.raises(ValueError, match="Invalid status"):
        await marker.mark_vocabulary(vocab.id, "invalid")


@pytest.mark.asyncio
async def test_mark_vocabulary_not_found(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    marker = Marker(repo)

    success = await marker.mark_vocabulary(9999, "known")
    assert success is False


@pytest.mark.asyncio
async def test_mark_sentence(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    marker = Marker(repo)

    sentence = await repo.add_sentence(german="Das ist ein Haus.", chinese="这是一座房子。")
    await repo.commit()

    success = await marker.mark_sentence(sentence.id, "learning")
    assert success is True

    updated = await repo.get_sentence(sentence.id)
    assert updated is not None
    assert updated.status == "learning"


@pytest.mark.asyncio
async def test_mark_item_dispatch(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    marker = Marker(repo)

    vocab = await repo.add_vocabulary(german="Baum", chinese="树")
    await repo.commit()

    success = await marker.mark_item("vocabulary", vocab.id, "known")
    assert success is True

    with pytest.raises(ValueError, match="Unknown item type"):
        await marker.mark_item("invalid_type", 1, "known")
