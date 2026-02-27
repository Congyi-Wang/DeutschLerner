"""Abstract base class for notification channels."""

from abc import ABC, abstractmethod


class Notifier(ABC):
    """Base class for all notification channels."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Channel name: 'discord', 'whatsapp'."""
        ...

    @abstractmethod
    async def send(self, title: str, content: str) -> bool:
        """Send a notification message.

        Args:
            title: Message title/subject.
            content: Formatted message body.

        Returns:
            True if sent successfully, False otherwise.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the notification channel is accessible."""
        ...
