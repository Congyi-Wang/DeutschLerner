"""SQLAlchemy ORM models for DeutschLerner."""

from datetime import datetime

from sqlalchemy import Integer, String, Text, DateTime, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all ORM models."""

    pass


class Vocabulary(Base):
    """Core vocabulary tracking table."""

    __tablename__ = "vocabulary"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    german: Mapped[str] = mapped_column(String, nullable=False, unique=True)
    chinese: Mapped[str] = mapped_column(String, nullable=False)
    phonetic: Mapped[str | None] = mapped_column(String, nullable=True)
    part_of_speech: Mapped[str | None] = mapped_column(String, nullable=True)
    gender: Mapped[str | None] = mapped_column(String, nullable=True)
    example: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="unknown")
    difficulty: Mapped[int] = mapped_column(Integer, default=0)
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class Sentence(Base):
    """Sentence tracking table."""

    __tablename__ = "sentences"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    german: Mapped[str] = mapped_column(Text, nullable=False)
    chinese: Mapped[str] = mapped_column(Text, nullable=False)
    grammar_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    source_topic: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="unknown")
    review_count: Mapped[int] = mapped_column(Integer, default=0)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )


class TopicHistory(Base):
    """Topic history for heartbeat dedup."""

    __tablename__ = "topic_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    topic: Mapped[str] = mapped_column(String, nullable=False)
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    source: Mapped[str] = mapped_column(String, default="heartbeat")
    sent_via: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class LearningSession(Base):
    """Learning sessions log."""

    __tablename__ = "learning_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_type: Mapped[str] = mapped_column(String, nullable=False)
    user_input: Mapped[str | None] = mapped_column(Text, nullable=True)
    ai_provider: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    vocab_added: Mapped[int] = mapped_column(Integer, default=0)
    sentences_added: Mapped[int] = mapped_column(Integer, default=0)
    duration_seconds: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class DailyChapter(Base):
    """Pre-generated daily chapters from heartbeat."""

    __tablename__ = "daily_chapters"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    date: Mapped[str] = mapped_column(String, nullable=False, unique=True)  # YYYY-MM-DD
    category: Mapped[str | None] = mapped_column(String, nullable=True)
    content_json: Mapped[str] = mapped_column(Text, nullable=False)  # Full TopicResult as JSON
    vocab_added: Mapped[int] = mapped_column(Integer, default=0)
    sentences_added: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class AppConfig(Base):
    """Runtime configuration store."""

    __tablename__ = "app_config"

    key: Mapped[str] = mapped_column(String, primary_key=True)
    value: Mapped[str] = mapped_column(Text, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now()
    )
