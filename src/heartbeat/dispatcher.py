"""Route generated topics to notification channels."""

import logging
from dataclasses import dataclass

from src.core.topic_generator import TopicResult
from src.notifications.base import Notifier
from src.notifications.discord_bot import DiscordNotifier, format_topic_for_discord
from src.notifications.whatsapp import WhatsAppNotifier, format_topic_for_whatsapp

logger = logging.getLogger(__name__)


@dataclass
class DispatchResult:
    """Result of dispatching a topic to channels."""

    channels_attempted: list[str]
    channels_succeeded: list[str]
    channels_failed: list[str]


class Dispatcher:
    """Dispatch topics to configured notification channels."""

    def __init__(self, config: dict) -> None:
        self._notifiers: list[Notifier] = []
        self._init_channels(config)

    def _init_channels(self, config: dict) -> None:
        """Initialize notification channels from config."""
        channels = config.get("channels", {})

        # Discord
        discord_config = channels.get("discord", {})
        if discord_config.get("enabled", False):
            token = discord_config.get("bot_token", "")
            channel_id = discord_config.get("channel_id", "")
            if token and channel_id:
                self._notifiers.append(
                    DiscordNotifier(bot_token=token, channel_id=int(channel_id))
                )
                logger.info("Discord notification channel enabled")

        # WhatsApp
        wa_config = channels.get("whatsapp", {})
        if wa_config.get("enabled", False):
            sid = wa_config.get("account_sid", "")
            token = wa_config.get("auth_token", "")
            from_num = wa_config.get("from_number", "")
            to_num = wa_config.get("to_number", "")
            if all([sid, token, from_num, to_num]):
                self._notifiers.append(
                    WhatsAppNotifier(
                        account_sid=sid,
                        auth_token=token,
                        from_number=from_num,
                        to_number=to_num,
                    )
                )
                logger.info("WhatsApp notification channel enabled")

    async def dispatch(self, topic: TopicResult) -> DispatchResult:
        """Send a topic to all enabled notification channels."""
        title = f"{topic.topic_title_de} — {topic.topic_title_cn}"
        topic_data = {
            "summary_cn": topic.summary_cn,
            "vocabulary": topic.vocabulary,
            "sentences": topic.sentences,
            "grammar_tips": topic.grammar_tips,
            "exercise": topic.exercise,
        }

        result = DispatchResult(
            channels_attempted=[],
            channels_succeeded=[],
            channels_failed=[],
        )

        for notifier in self._notifiers:
            result.channels_attempted.append(notifier.name)

            # Format content per channel
            if isinstance(notifier, DiscordNotifier):
                content = format_topic_for_discord(topic_data)
            elif isinstance(notifier, WhatsAppNotifier):
                content = format_topic_for_whatsapp(topic_data)
            else:
                content = topic.raw_content

            success = await notifier.send(title, content)
            if success:
                result.channels_succeeded.append(notifier.name)
            else:
                result.channels_failed.append(notifier.name)

        return result

    @property
    def channel_names(self) -> list[str]:
        """List names of enabled channels."""
        return [n.name for n in self._notifiers]
