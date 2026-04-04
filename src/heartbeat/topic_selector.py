"""Random topic selection + history dedup check + A1 curriculum support."""

import logging
import random

from src.heartbeat.curriculum import A1Module, get_current_module
from src.storage.repository import Repository

logger = logging.getLogger(__name__)

TOPIC_CATEGORIES = [
    "daily_life",
    "grammar",
    "culture",
    "business",
    "travel",
    "academic",
    "idioms",
    "news_vocabulary",
]

CATEGORY_LABELS = {
    "daily_life": "日常生活",
    "grammar": "语法",
    "culture": "文化",
    "business": "商务德语",
    "travel": "旅游",
    "academic": "学术",
    "idioms": "习语和谚语",
    "news_vocabulary": "新闻词汇",
}


class TopicSelector:
    """Select a topic category with weighted randomness and dedup."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def select_topic_for_level(self) -> tuple[str, str, A1Module | None]:
        """Select a topic based on user's current level.

        Returns:
            (topic_description, category_string, module_or_none)
            If A1: picks from module's topic list, avoiding recently used.
            If A1 completed: falls back to existing random category selection.
        """
        vocab_count = await self.repo.count_vocabulary()
        module = get_current_module(vocab_count)

        if module is None:
            # A1 completed — fall back to random categories
            category = await self.select_category()
            return (category, category, None)

        # A1 mode: pick a topic from the current module
        recent_titles = await self.repo.get_recent_topic_titles(limit=20)
        recent_lower = {t.lower() for t in recent_titles}

        # Prefer topics not recently used
        available = [
            t for t in module.topics
            if not any(keyword in title for title in recent_lower for keyword in t.lower().split()[:3])
        ]
        if not available:
            available = module.topics

        topic = random.choice(available)
        category = f"A1_M{module.id}_{module.name_cn}"
        logger.info("A1 mode: module %d (%s), topic: %s, vocab: %d/%d",
                     module.id, module.name_cn, topic, vocab_count, module.target_vocab)
        return (topic, category, module)

    async def select_category(self) -> str:
        """Pick a category, weighting less-used categories higher.

        Returns:
            A category string from TOPIC_CATEGORIES.
        """
        used = await self.repo.get_used_categories()
        max_count = max(used.values()) if used else 0

        # Weight = (max_count + 1 - category_count)
        weights = []
        for cat in TOPIC_CATEGORIES:
            count = used.get(cat, 0)
            weight = max(1, max_count + 1 - count)
            weights.append(weight)

        return random.choices(TOPIC_CATEGORIES, weights=weights, k=1)[0]

    async def is_duplicate(self, topic_title: str) -> bool:
        """Check if this topic title has already been sent."""
        return await self.repo.topic_exists(topic_title)

    async def record_topic(
        self, topic: str, category: str, content: str, sent_via: str
    ) -> None:
        """Record a topic in history after sending."""
        await self.repo.add_topic_history(
            topic=topic,
            category=category,
            content=content,
            source="heartbeat",
            sent_via=sent_via,
        )
        await self.repo.commit()
