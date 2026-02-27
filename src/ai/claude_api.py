"""Anthropic Claude API provider."""

import logging
from typing import AsyncIterator

import anthropic

from src.ai.base import AIProvider, AIResponse

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "claude-sonnet-4-20250514"


class ClaudeProvider(AIProvider):
    """AI provider using the Anthropic Claude API."""

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self._client = anthropic.AsyncAnthropic(api_key=api_key)
        self._model = model or DEFAULT_MODEL

    @property
    def name(self) -> str:
        return "claude"

    async def generate(self, system_prompt: str, user_message: str) -> AIResponse:
        """Generate a complete response via Claude API."""
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        )
        content = response.content[0].text
        tokens = (response.usage.input_tokens or 0) + (response.usage.output_tokens or 0)
        return AIResponse(
            content=content,
            provider=self.name,
            model=self._model,
            tokens_used=tokens,
        )

    async def stream(self, system_prompt: str, user_message: str) -> AsyncIterator[str]:
        """Stream response chunks from Claude API."""
        async with self._client.messages.stream(
            model=self._model,
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": user_message}],
        ) as stream:
            async for text in stream.text_stream:
                yield text

    async def health_check(self) -> bool:
        """Check if the Claude API is accessible."""
        try:
            response = await self._client.messages.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return len(response.content) > 0
        except Exception:
            logger.exception("Claude health check failed")
            return False
