"""WhatsApp notification channel via Twilio."""

import logging

from twilio.rest import Client as TwilioClient

from src.notifications.base import Notifier

logger = logging.getLogger(__name__)

MAX_WHATSAPP_LENGTH = 1600


class WhatsAppNotifier(Notifier):
    """Send learning content via WhatsApp using the Twilio API."""

    def __init__(
        self,
        account_sid: str,
        auth_token: str,
        from_number: str,
        to_number: str,
    ) -> None:
        self._client = TwilioClient(account_sid, auth_token)
        self._from = from_number
        self._to = to_number

    @property
    def name(self) -> str:
        return "whatsapp"

    async def send(self, title: str, content: str) -> bool:
        """Send a formatted text message via WhatsApp."""
        try:
            body = f"📚 *{title}*\n\n{content}"
            if len(body) > MAX_WHATSAPP_LENGTH:
                body = body[:MAX_WHATSAPP_LENGTH - 3] + "..."

            # Twilio client is synchronous
            message = self._client.messages.create(
                body=body,
                from_=self._from,
                to=self._to,
            )
            logger.info("WhatsApp message sent: SID=%s", message.sid)
            return True

        except Exception:
            logger.exception("Failed to send WhatsApp message")
            return False

    async def health_check(self) -> bool:
        """Check if Twilio credentials are valid."""
        try:
            self._client.api.accounts(self._client.account_sid).fetch()
            return True
        except Exception:
            logger.exception("WhatsApp health check failed")
            return False


def format_topic_for_whatsapp(topic_data: dict) -> str:
    """Format a topic result into a WhatsApp-friendly plain text string."""
    parts = []

    if topic_data.get("summary_cn"):
        parts.append(topic_data["summary_cn"])
        parts.append("")

    # Vocabulary
    vocab = topic_data.get("vocabulary", [])
    if vocab:
        parts.append("📖 *核心词汇*")
        for v in vocab:
            gender = f" ({v['gender']})" if v.get("gender") else ""
            parts.append(f"• {v['german']}{gender} — {v.get('chinese', '')}")
        parts.append("")

    # Sentences
    sentences = topic_data.get("sentences", [])
    if sentences:
        parts.append("✍️ *重点句型*")
        for s in sentences:
            parts.append(f"• {s['german']}")
            parts.append(f"  {s.get('chinese', '')}")
        parts.append("")

    # Grammar tips
    if topic_data.get("grammar_tips"):
        parts.append(f"📝 {topic_data['grammar_tips']}")

    return "\n".join(parts)
