"""MemoryManager: CRUD for learned items + dedup + export/import."""

import json
import logging
from datetime import datetime

from src.storage.repository import Repository

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages the user's learning memory — vocabulary and sentences."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def get_known_words(self) -> list[str]:
        """Get list of German words the user already knows."""
        items = await self.repo.list_vocabulary(status="known", limit=10000)
        return [item.german for item in items]

    async def get_learning_words(self) -> list[str]:
        """Get list of German words currently being learned."""
        items = await self.repo.list_vocabulary(status="learning", limit=10000)
        return [item.german for item in items]

    async def get_unknown_words(self) -> list[str]:
        """Get list of German words not yet learned."""
        items = await self.repo.list_vocabulary(status="unknown", limit=10000)
        return [item.german for item in items]

    async def build_context(self) -> str:
        """Build a memory context string for AI prompts.

        This tells the AI what the user already knows so it can avoid
        repeating known vocabulary and build on existing knowledge.
        Includes current level/module info for level-aware generation.
        """
        from src.heartbeat.curriculum import get_current_module

        known = await self.get_known_words()
        learning = await self.get_learning_words()
        stats = await self.repo.get_stats()
        vocab_count = stats["vocabulary"]["total"]

        parts = []
        parts.append(f"学习进度: {stats['vocabulary']['known']}个已掌握, "
                      f"{stats['vocabulary']['learning']}个学习中, "
                      f"{stats['vocabulary']['unknown']}个未学习")

        # Add level context
        module = get_current_module(vocab_count)
        if module is not None:
            parts.append(f"当前水平: A1 模块{module.id} — {module.name_cn}")
            parts.append(f"模块说明: {module.description_cn}")
            parts.append(f"当前语法重点: {', '.join(module.grammar_focus)}")
            parts.append("请根据用户当前A1水平生成内容，词汇和句子要简单，句子不超过8个词。")
        else:
            parts.append("用户已完成A1，可以使用更丰富的词汇和语法。")

        if known:
            sample = known[:50]
            parts.append(f"已掌握的词汇（部分）: {', '.join(sample)}")

        if learning:
            sample = learning[:30]
            parts.append(f"正在学习的词汇: {', '.join(sample)}")

        parts.append("请避免重复已掌握的词汇，可以在句子中使用它们来巩固。")
        return "\n".join(parts)

    async def add_vocabulary_batch(
        self, items: list[dict], source_topic: str | None = None
    ) -> int:
        """Add multiple vocabulary items, deduplicating by German word.

        Returns the number of new items added.
        """
        added = 0
        for item in items:
            german = item.get("german", "").strip()
            if not german:
                continue
            existing = await self.repo.get_vocabulary_by_german(german)
            if existing:
                logger.debug("Vocabulary '%s' already exists, skipping", german)
                continue
            await self.repo.add_vocabulary(
                german=german,
                chinese=item.get("chinese", ""),
                phonetic=item.get("phonetic"),
                part_of_speech=item.get("part_of_speech"),
                gender=item.get("gender"),
                example=item.get("example_de", item.get("example")),
                status="unknown",
                difficulty=item.get("difficulty", 0),
            )
            added += 1
        return added

    async def add_sentences_batch(
        self, sentences: list[dict], source_topic: str | None = None
    ) -> int:
        """Add multiple sentences.

        Returns the number of new sentences added.
        """
        added = 0
        for s in sentences:
            german = s.get("german", "").strip()
            if not german:
                continue
            await self.repo.add_sentence(
                german=german,
                chinese=s.get("chinese", ""),
                grammar_notes=s.get("grammar_note", s.get("grammar_notes")),
                source_topic=source_topic,
                status="unknown",
            )
            added += 1
        return added

    async def export_data(self) -> dict:
        """Export all learning data as a dictionary."""
        return await self.repo.export_all()

    async def import_data(self, data: dict) -> dict[str, int]:
        """Import learning data from a dictionary.

        Returns counts of imported items.
        """
        counts = {"vocabulary": 0, "sentences": 0}

        for item in data.get("vocabulary", []):
            german = item.get("german", "").strip()
            if not german:
                continue
            existing = await self.repo.get_vocabulary_by_german(german)
            if existing:
                continue
            await self.repo.add_vocabulary(
                german=german,
                chinese=item.get("chinese", ""),
                phonetic=item.get("phonetic"),
                part_of_speech=item.get("part_of_speech"),
                gender=item.get("gender"),
                example=item.get("example"),
                status=item.get("status", "unknown"),
                difficulty=item.get("difficulty", 0),
                review_count=item.get("review_count", 0),
            )
            counts["vocabulary"] += 1

        for item in data.get("sentences", []):
            german = item.get("german", "").strip()
            if not german:
                continue
            await self.repo.add_sentence(
                german=german,
                chinese=item.get("chinese", ""),
                grammar_notes=item.get("grammar_notes"),
                source_topic=item.get("source_topic"),
                status=item.get("status", "unknown"),
                review_count=item.get("review_count", 0),
            )
            counts["sentences"] += 1

        await self.repo.commit()
        return counts

    async def get_stats(self) -> dict:
        """Get learning statistics."""
        return await self.repo.get_stats()
