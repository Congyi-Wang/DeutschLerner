"""Data access layer — all database queries live here."""

import logging
from datetime import datetime

from sqlalchemy import select, func, delete, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.storage.models import (
    AppConfig,
    LearningSession,
    Sentence,
    TopicHistory,
    Vocabulary,
)

logger = logging.getLogger(__name__)


class Repository:
    """Data access layer for all DeutschLerner tables."""

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    # ── Vocabulary ──────────────────────────────────────────────

    async def add_vocabulary(self, **kwargs: object) -> Vocabulary:
        """Add a new vocabulary item. Skips if german word already exists."""
        existing = await self.get_vocabulary_by_german(str(kwargs.get("german", "")))
        if existing:
            logger.debug("Vocabulary '%s' already exists, skipping", kwargs.get("german"))
            return existing
        item = Vocabulary(**kwargs)
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_vocabulary(self, vocab_id: int) -> Vocabulary | None:
        """Get a single vocabulary item by ID."""
        return await self.session.get(Vocabulary, vocab_id)

    async def get_vocabulary_by_german(self, german: str) -> Vocabulary | None:
        """Look up vocabulary by the German word."""
        result = await self.session.execute(
            select(Vocabulary).where(Vocabulary.german == german)
        )
        return result.scalar_one_or_none()

    async def list_vocabulary(
        self, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[Vocabulary]:
        """List vocabulary items with optional status filter."""
        query = select(Vocabulary).order_by(Vocabulary.created_at.desc())
        if status:
            query = query.where(Vocabulary.status == status)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_vocabulary(self, vocab_id: int, **kwargs: object) -> Vocabulary | None:
        """Update a vocabulary item."""
        item = await self.get_vocabulary(vocab_id)
        if item is None:
            return None
        for key, value in kwargs.items():
            setattr(item, key, value)
        item.updated_at = datetime.utcnow()
        await self.session.flush()
        return item

    async def delete_vocabulary(self, vocab_id: int) -> bool:
        """Delete a vocabulary item by ID."""
        result = await self.session.execute(
            delete(Vocabulary).where(Vocabulary.id == vocab_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def count_vocabulary(self, status: str | None = None) -> int:
        """Count vocabulary items, optionally filtered by status."""
        query = select(func.count(Vocabulary.id))
        if status:
            query = query.where(Vocabulary.status == status)
        result = await self.session.execute(query)
        return result.scalar_one()

    async def get_review_vocabulary(self, count: int = 10) -> list[Vocabulary]:
        """Get vocabulary items for review — prioritize unknown/learning with low review_count."""
        query = (
            select(Vocabulary)
            .where(Vocabulary.status.in_(["unknown", "learning"]))
            .order_by(Vocabulary.review_count.asc(), Vocabulary.created_at.asc())
            .limit(count)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ── Sentences ───────────────────────────────────────────────

    async def add_sentence(self, **kwargs: object) -> Sentence:
        """Add a new sentence."""
        item = Sentence(**kwargs)
        self.session.add(item)
        await self.session.flush()
        return item

    async def get_sentence(self, sentence_id: int) -> Sentence | None:
        """Get a single sentence by ID."""
        return await self.session.get(Sentence, sentence_id)

    async def list_sentences(
        self, status: str | None = None, limit: int = 100, offset: int = 0
    ) -> list[Sentence]:
        """List sentences with optional status filter."""
        query = select(Sentence).order_by(Sentence.created_at.desc())
        if status:
            query = query.where(Sentence.status == status)
        query = query.limit(limit).offset(offset)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def update_sentence(self, sentence_id: int, **kwargs: object) -> Sentence | None:
        """Update a sentence."""
        item = await self.get_sentence(sentence_id)
        if item is None:
            return None
        for key, value in kwargs.items():
            setattr(item, key, value)
        item.updated_at = datetime.utcnow()
        await self.session.flush()
        return item

    async def delete_sentence(self, sentence_id: int) -> bool:
        """Delete a sentence by ID."""
        result = await self.session.execute(
            delete(Sentence).where(Sentence.id == sentence_id)
        )
        await self.session.flush()
        return result.rowcount > 0

    async def count_sentences(self, status: str | None = None) -> int:
        """Count sentences, optionally filtered by status."""
        query = select(func.count(Sentence.id))
        if status:
            query = query.where(Sentence.status == status)
        result = await self.session.execute(query)
        return result.scalar_one()

    # ── Topic History ───────────────────────────────────────────

    async def add_topic_history(self, **kwargs: object) -> TopicHistory:
        """Record a topic in history."""
        item = TopicHistory(**kwargs)
        self.session.add(item)
        await self.session.flush()
        return item

    async def topic_exists(self, topic: str) -> bool:
        """Check if a topic has already been sent."""
        result = await self.session.execute(
            select(func.count(TopicHistory.id)).where(TopicHistory.topic == topic)
        )
        return result.scalar_one() > 0

    async def list_topic_history(self, limit: int = 50) -> list[TopicHistory]:
        """List recent topic history."""
        query = select(TopicHistory).order_by(TopicHistory.created_at.desc()).limit(limit)
        result = await self.session.execute(query)
        return list(result.scalars().all())

    async def get_used_categories(self) -> dict[str, int]:
        """Get count of topics per category."""
        query = select(
            TopicHistory.category, func.count(TopicHistory.id)
        ).group_by(TopicHistory.category)
        result = await self.session.execute(query)
        return {row[0] or "uncategorized": row[1] for row in result.all()}

    # ── Learning Sessions ───────────────────────────────────────

    async def add_learning_session(self, **kwargs: object) -> LearningSession:
        """Log a learning session."""
        item = LearningSession(**kwargs)
        self.session.add(item)
        await self.session.flush()
        return item

    async def list_learning_sessions(self, limit: int = 20) -> list[LearningSession]:
        """List recent learning sessions."""
        query = (
            select(LearningSession)
            .order_by(LearningSession.created_at.desc())
            .limit(limit)
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())

    # ── App Config ──────────────────────────────────────────────

    async def get_config(self, key: str) -> str | None:
        """Get a runtime config value."""
        item = await self.session.get(AppConfig, key)
        return item.value if item else None

    async def set_config(self, key: str, value: str) -> None:
        """Set a runtime config value (upsert)."""
        existing = await self.session.get(AppConfig, key)
        if existing:
            existing.value = value
            existing.updated_at = datetime.utcnow()
        else:
            self.session.add(AppConfig(key=key, value=value))
        await self.session.flush()

    # ── Bulk / Export ───────────────────────────────────────────

    async def export_all(self) -> dict:
        """Export all data as a dictionary."""
        vocab = await self.list_vocabulary(limit=10000)
        sentences = await self.list_sentences(limit=10000)
        topics = await self.list_topic_history(limit=10000)
        sessions = await self.list_learning_sessions(limit=10000)

        def serialize(item: object) -> dict:
            d = {}
            for col in item.__table__.columns:
                val = getattr(item, col.name)
                if isinstance(val, datetime):
                    val = val.isoformat()
                d[col.name] = val
            return d

        return {
            "vocabulary": [serialize(v) for v in vocab],
            "sentences": [serialize(s) for s in sentences],
            "topic_history": [serialize(t) for t in topics],
            "learning_sessions": [serialize(s) for s in sessions],
        }

    # ── Stats ───────────────────────────────────────────────────

    async def get_stats(self) -> dict:
        """Get overall learning statistics."""
        return {
            "vocabulary": {
                "total": await self.count_vocabulary(),
                "known": await self.count_vocabulary("known"),
                "learning": await self.count_vocabulary("learning"),
                "unknown": await self.count_vocabulary("unknown"),
            },
            "sentences": {
                "total": await self.count_sentences(),
                "known": await self.count_sentences("known"),
                "learning": await self.count_sentences("learning"),
                "unknown": await self.count_sentences("unknown"),
            },
        }

    # ── Session Management ──────────────────────────────────────

    async def commit(self) -> None:
        """Commit the current transaction."""
        await self.session.commit()

    async def rollback(self) -> None:
        """Rollback the current transaction."""
        await self.session.rollback()

    async def close(self) -> None:
        """Close the session."""
        await self.session.close()
