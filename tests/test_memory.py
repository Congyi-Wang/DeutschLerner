"""Test memory dedup, export, import."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.memory import MemoryManager
from src.storage.repository import Repository


@pytest.mark.asyncio
async def test_add_vocabulary_batch(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    memory = MemoryManager(repo)

    items = [
        {"german": "Hund", "chinese": "狗", "gender": "der", "part_of_speech": "noun"},
        {"german": "Katze", "chinese": "猫", "gender": "die", "part_of_speech": "noun"},
    ]
    added = await memory.add_vocabulary_batch(items)
    assert added == 2


@pytest.mark.asyncio
async def test_add_vocabulary_batch_dedup(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    memory = MemoryManager(repo)

    items = [{"german": "Hund", "chinese": "狗"}]
    added1 = await memory.add_vocabulary_batch(items)
    added2 = await memory.add_vocabulary_batch(items)

    assert added1 == 1
    assert added2 == 0  # Duplicate


@pytest.mark.asyncio
async def test_add_sentences_batch(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    memory = MemoryManager(repo)

    sentences = [
        {"german": "Der Hund ist groß.", "chinese": "这只狗很大。", "grammar_note": "形容词用法"},
    ]
    added = await memory.add_sentences_batch(sentences)
    assert added == 1


@pytest.mark.asyncio
async def test_build_context(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    memory = MemoryManager(repo)

    await repo.add_vocabulary(german="Haus", chinese="房子", status="known")
    await repo.add_vocabulary(german="Auto", chinese="汽车", status="learning")
    await repo.commit()

    context = await memory.build_context()
    assert "Haus" in context
    assert "Auto" in context
    assert "已掌握" in context


@pytest.mark.asyncio
async def test_export_import_roundtrip(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    memory = MemoryManager(repo)

    await repo.add_vocabulary(german="Tisch", chinese="桌子", status="known")
    await repo.add_sentence(german="Der Tisch ist groß.", chinese="桌子很大。")
    await repo.commit()

    data = await memory.export_data()
    assert len(data["vocabulary"]) == 1
    assert len(data["sentences"]) == 1

    # Import into fresh memory (same DB, but items already exist)
    # Vocabulary should be deduped, sentences will be added again
    counts = await memory.import_data(data)
    assert counts["vocabulary"] == 0  # Already exists


@pytest.mark.asyncio
async def test_get_stats(db_session: AsyncSession) -> None:
    repo = Repository(db_session)
    memory = MemoryManager(repo)

    await repo.add_vocabulary(german="Hund", chinese="狗", status="known")
    await repo.add_vocabulary(german="Katze", chinese="猫", status="unknown")
    await repo.commit()

    stats = await memory.get_stats()
    assert stats["vocabulary"]["total"] == 2
    assert stats["vocabulary"]["known"] == 1
    assert stats["vocabulary"]["unknown"] == 1
