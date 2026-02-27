"""Mark vocabulary/sentences as known/unknown/learning."""

import logging
from datetime import datetime

from src.storage.repository import Repository

logger = logging.getLogger(__name__)

VALID_STATUSES = {"known", "unknown", "learning"}


class Marker:
    """Handles status transitions for vocabulary and sentences."""

    def __init__(self, repo: Repository) -> None:
        self.repo = repo

    async def mark_vocabulary(self, vocab_id: int, status: str) -> bool:
        """Mark a vocabulary item with a new status.

        Args:
            vocab_id: The vocabulary item ID.
            status: One of 'known', 'unknown', 'learning'.

        Returns:
            True if the item was updated, False if not found.

        Raises:
            ValueError: If the status is invalid.
        """
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

        item = await self.repo.get_vocabulary(vocab_id)
        if item is None:
            logger.warning("Vocabulary ID %d not found", vocab_id)
            return False

        old_status = item.status
        update_fields: dict = {"status": status}

        if status in ("known", "learning"):
            update_fields["review_count"] = item.review_count + 1
            update_fields["last_reviewed_at"] = datetime.utcnow()

        await self.repo.update_vocabulary(vocab_id, **update_fields)
        logger.info("Vocabulary #%d: %s → %s", vocab_id, old_status, status)
        return True

    async def mark_sentence(self, sentence_id: int, status: str) -> bool:
        """Mark a sentence with a new status.

        Args:
            sentence_id: The sentence ID.
            status: One of 'known', 'unknown', 'learning'.

        Returns:
            True if the item was updated, False if not found.

        Raises:
            ValueError: If the status is invalid.
        """
        if status not in VALID_STATUSES:
            raise ValueError(f"Invalid status '{status}'. Must be one of: {VALID_STATUSES}")

        item = await self.repo.get_sentence(sentence_id)
        if item is None:
            logger.warning("Sentence ID %d not found", sentence_id)
            return False

        old_status = item.status
        update_fields: dict = {"status": status}

        if status in ("known", "learning"):
            update_fields["review_count"] = item.review_count + 1
            update_fields["last_reviewed_at"] = datetime.utcnow()

        await self.repo.update_sentence(sentence_id, **update_fields)
        logger.info("Sentence #%d: %s → %s", sentence_id, old_status, status)
        return True

    async def mark_item(self, item_type: str, item_id: int, status: str) -> bool:
        """Generic mark method — dispatches to vocabulary or sentence marker.

        Args:
            item_type: Either 'vocabulary' or 'sentence'.
            item_id: The item ID.
            status: One of 'known', 'unknown', 'learning'.
        """
        match item_type:
            case "vocabulary":
                return await self.mark_vocabulary(item_id, status)
            case "sentence":
                return await self.mark_sentence(item_id, status)
            case _:
                raise ValueError(f"Unknown item type '{item_type}'. Use 'vocabulary' or 'sentence'.")
