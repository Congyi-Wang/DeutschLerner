"""LearningEngine: orchestrates learning sessions."""

import logging
import time
from dataclasses import dataclass, field

from src.ai.base import AIProvider
from src.core.marker import Marker
from src.core.memory import MemoryManager
from src.core.topic_generator import TopicGenerator, TopicResult
from src.storage.repository import Repository

logger = logging.getLogger(__name__)


@dataclass
class LearningResult:
    """Result of a learning session."""

    topic: TopicResult
    vocab_added: int = 0
    sentences_added: int = 0
    duration_seconds: int = 0


class LearningEngine:
    """Central orchestrator for all learning activities."""

    def __init__(
        self,
        ai_provider: AIProvider,
        memory: MemoryManager,
        marker: Marker,
        repo: Repository,
    ) -> None:
        self.ai = ai_provider
        self.memory = memory
        self.marker = marker
        self.repo = repo
        self.topic_gen = TopicGenerator(ai_provider)

    async def learn_topic(self, user_input: str) -> LearningResult:
        """Main learning flow:
        1. Load user's current vocabulary status from memory
        2. Build context-aware prompt
        3. Generate topic content via AI
        4. Extract vocabulary and sentences
        5. Auto-mark new items as 'unknown'
        6. Return structured result
        """
        start = time.time()

        # Build memory context
        memory_context = await self.memory.build_context()

        # Generate topic
        topic = await self.topic_gen.generate_topic(user_input, memory_context)

        # Store vocabulary and sentences
        vocab_added = await self.memory.add_vocabulary_batch(
            topic.vocabulary, source_topic=topic.topic_title_de
        )
        sentences_added = await self.memory.add_sentences_batch(
            topic.sentences, source_topic=topic.topic_title_de
        )

        duration = int(time.time() - start)

        # Log the session
        await self.repo.add_learning_session(
            session_type="topic",
            user_input=user_input,
            ai_provider=topic.provider,
            content=topic.raw_content,
            vocab_added=vocab_added,
            sentences_added=sentences_added,
            duration_seconds=duration,
        )
        await self.repo.commit()

        logger.info(
            "Topic '%s' generated: +%d vocab, +%d sentences (%ds)",
            topic.topic_title_de,
            vocab_added,
            sentences_added,
            duration,
        )

        return LearningResult(
            topic=topic,
            vocab_added=vocab_added,
            sentences_added=sentences_added,
            duration_seconds=duration,
        )

    async def review_vocabulary(self, count: int = 10) -> list[dict]:
        """Get vocabulary items for review, prioritizing low review_count."""
        items = await self.repo.get_review_vocabulary(count)
        return [
            {
                "id": item.id,
                "german": item.german,
                "chinese": item.chinese,
                "gender": item.gender,
                "part_of_speech": item.part_of_speech,
                "example": item.example,
                "status": item.status,
                "review_count": item.review_count,
            }
            for item in items
        ]

    async def mark_item(self, item_type: str, item_id: int, status: str) -> bool:
        """Mark a vocabulary word or sentence as known/unknown/learning."""
        result = await self.marker.mark_item(item_type, item_id, status)
        if result:
            await self.repo.commit()
        return result
