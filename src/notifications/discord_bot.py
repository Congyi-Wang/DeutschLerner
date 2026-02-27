"""Discord bot notification channel."""

import logging

import discord

from src.notifications.base import Notifier

logger = logging.getLogger(__name__)

MAX_EMBED_DESCRIPTION = 4096


class DiscordNotifier(Notifier):
    """Send learning content to a Discord channel via bot."""

    def __init__(self, bot_token: str, channel_id: int) -> None:
        self._token = bot_token
        self._channel_id = channel_id
        self._client: discord.Client | None = None

    @property
    def name(self) -> str:
        return "discord"

    async def _get_client(self) -> discord.Client:
        """Get or create the Discord client."""
        if self._client is None:
            intents = discord.Intents.default()
            self._client = discord.Client(intents=intents)
        return self._client

    async def send(self, title: str, content: str) -> bool:
        """Send a rich embed message to the configured Discord channel."""
        try:
            client = await self._get_client()

            async with client:
                await client.login(self._token)

                channel = await client.fetch_channel(self._channel_id)
                if not isinstance(channel, discord.TextChannel):
                    logger.error("Channel %d is not a text channel", self._channel_id)
                    return False

                # Build embed
                embed = discord.Embed(
                    title=f"📚 {title}",
                    description=content[:MAX_EMBED_DESCRIPTION],
                    color=discord.Color.blue(),
                )
                embed.set_footer(text="DeutschLerner — 每日德语学习")

                await channel.send(embed=embed)
                logger.info("Discord message sent to channel %d", self._channel_id)
                return True

        except Exception:
            logger.exception("Failed to send Discord message")
            return False

    async def health_check(self) -> bool:
        """Check if the Discord bot can authenticate."""
        try:
            client = await self._get_client()
            async with client:
                await client.login(self._token)
                return True
        except Exception:
            logger.exception("Discord health check failed")
            return False


def format_topic_for_discord(topic_data: dict) -> str:
    """Format a topic result into a Discord-friendly string."""
    parts = []

    if topic_data.get("summary_cn"):
        parts.append(f"**概述**: {topic_data['summary_cn']}\n")

    # Vocabulary
    vocab = topic_data.get("vocabulary", [])
    if vocab:
        parts.append("**📖 核心词汇**")
        for v in vocab:
            gender = f" ({v['gender']})" if v.get("gender") else ""
            parts.append(f"• **{v['german']}**{gender} — {v.get('chinese', '')}")
            if v.get("example_de"):
                parts.append(f"  _{v['example_de']}_")
        parts.append("")

    # Sentences
    sentences = topic_data.get("sentences", [])
    if sentences:
        parts.append("**✍️ 重点句型**")
        for s in sentences:
            parts.append(f"• **{s['german']}**")
            parts.append(f"  {s.get('chinese', '')}")
            if s.get("grammar_note"):
                parts.append(f"  💡 {s['grammar_note']}")
        parts.append("")

    # Grammar tips
    if topic_data.get("grammar_tips"):
        parts.append(f"**📝 语法提示**: {topic_data['grammar_tips']}\n")

    # Exercise
    if topic_data.get("exercise"):
        parts.append(f"**🎯 练习**: {topic_data['exercise']}")

    return "\n".join(parts)
