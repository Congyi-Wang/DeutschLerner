"""APScheduler integration for heartbeat."""

import json
import logging
from datetime import date, timedelta
from zoneinfo import ZoneInfo

from apscheduler.schedulers.asyncio import AsyncIOScheduler

from src.ai.factory import create_provider
from src.api.dependencies import get_current_provider_info
from src.core.memory import MemoryManager
from src.core.topic_generator import TopicGenerator
from src.heartbeat.dispatcher import Dispatcher
from src.heartbeat.topic_selector import TopicSelector
from src.storage.database import get_session
from src.storage.repository import Repository

logger = logging.getLogger(__name__)

MAX_DEDUP_RETRIES = 3


class HeartbeatScheduler:
    """Manages the scheduled heartbeat — generates and sends daily topics."""

    def __init__(self, config: dict, db_path: str = "data/deutsch_lerner.db") -> None:
        self._config = config
        self._db_path = db_path
        self._scheduler = AsyncIOScheduler()
        self._dispatcher = Dispatcher(config)
        self.running = False
        self._setup_schedule()

    def _setup_schedule(self) -> None:
        """Configure the scheduler from config."""
        schedule = self._config.get("schedule", {})
        schedule_type = schedule.get("type", "cron")
        timezone = schedule.get("timezone", "Europe/Berlin")

        if schedule_type == "cron":
            self._scheduler.add_job(
                self._heartbeat_job,
                "cron",
                hour=schedule.get("hour", 9),
                minute=schedule.get("minute", 0),
                timezone=ZoneInfo(timezone),
                id="heartbeat",
                replace_existing=True,
            )
        else:
            hours = schedule.get("hours", 24)
            self._scheduler.add_job(
                self._heartbeat_job,
                "interval",
                hours=hours,
                id="heartbeat",
                replace_existing=True,
            )

    def start(self) -> None:
        """Start the scheduler."""
        if not self.running:
            self._scheduler.start()
            self.running = True
            logger.info("Heartbeat scheduler started")

    def stop(self) -> None:
        """Stop the scheduler."""
        if self.running:
            self._scheduler.shutdown(wait=False)
            self.running = False
            logger.info("Heartbeat scheduler stopped")

    async def trigger_now(self) -> dict:
        """Manually trigger one heartbeat cycle."""
        return await self._heartbeat_job()

    async def _heartbeat_job(self) -> dict:
        """Execute one heartbeat cycle: generate topic, store as daily chapter, dispatch."""
        session = await get_session(self._db_path)
        try:
            repo = Repository(session)
            selector = TopicSelector(repo)

            # Get AI provider
            provider_info = get_current_provider_info()
            provider = create_provider(
                provider_info["provider"], provider_info.get("model")
            )
            topic_gen = TopicGenerator(provider)
            memory = MemoryManager(repo)

            # Select category and generate topic
            category = await selector.select_category()
            topic = None

            for attempt in range(MAX_DEDUP_RETRIES):
                topic = await topic_gen.generate_heartbeat_topic(category)
                if not await selector.is_duplicate(topic.topic_title_de):
                    break
                logger.info("Duplicate topic '%s', retrying (%d/%d)",
                            topic.topic_title_de, attempt + 1, MAX_DEDUP_RETRIES)
                if attempt == MAX_DEDUP_RETRIES - 1:
                    category = await selector.select_category()

            if topic is None:
                logger.error("Failed to generate a heartbeat topic")
                return {"status": "error", "reason": "generation_failed"}

            # Store vocabulary and sentences
            vocab_added = await memory.add_vocabulary_batch(
                topic.vocabulary, source_topic=topic.topic_title_de
            )
            sentences_added = await memory.add_sentences_batch(
                topic.sentences, source_topic=topic.topic_title_de
            )

            # Save as pre-generated daily chapter for tomorrow
            tomorrow = (date.today() + timedelta(days=1)).isoformat()
            chapter_data = {
                "topic_title_de": topic.topic_title_de,
                "topic_title_cn": topic.topic_title_cn,
                "summary_cn": topic.summary_cn,
                "vocabulary": topic.vocabulary,
                "sentences": topic.sentences,
                "grammar_tips": topic.grammar_tips,
                "grammar_analysis": topic.grammar_analysis if hasattr(topic, "grammar_analysis") else None,
                "exercise": topic.exercise,
                "category": category,
                "provider": topic.provider,
            }
            await repo.save_daily_chapter(
                date_str=tomorrow,
                category=category,
                content_json=json.dumps(chapter_data, ensure_ascii=False),
                vocab_added=vocab_added,
                sentences_added=sentences_added,
            )
            logger.info("Pre-generated daily chapter saved for %s", tomorrow)

            await repo.commit()

            # Dispatch to channels
            dispatch_result = await self._dispatcher.dispatch(topic)

            # Record in history
            sent_via = ",".join(dispatch_result.channels_succeeded) or "none"
            await selector.record_topic(
                topic=topic.topic_title_de,
                category=category,
                content=topic.raw_content,
                sent_via=sent_via,
            )

            result = {
                "status": "ok",
                "topic": topic.topic_title_de,
                "category": category,
                "vocab_added": vocab_added,
                "sentences_added": sentences_added,
                "chapter_date": tomorrow,
                "channels": {
                    "succeeded": dispatch_result.channels_succeeded,
                    "failed": dispatch_result.channels_failed,
                },
            }
            logger.info("Heartbeat complete: %s", result)
            return result

        except Exception:
            logger.exception("Heartbeat job failed")
            await session.rollback()
            return {"status": "error", "reason": "exception"}
        finally:
            await session.close()
