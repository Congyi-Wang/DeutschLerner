"""Moonshot Kimi API provider (OpenAI-compatible)."""

import logging
from typing import AsyncIterator

import openai

from src.ai.base import AIProvider, AIResponse

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "moonshot-v1-8k"
BASE_URL = "https://api.moonshot.cn/v1"


class KimiProvider(AIProvider):
    """AI provider using the Moonshot (Kimi) API — OpenAI-compatible."""

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self._client = openai.AsyncOpenAI(api_key=api_key, base_url=BASE_URL)
        self._model = model or DEFAULT_MODEL

    @property
    def name(self) -> str:
        return "kimi"

    async def generate(self, system_prompt: str, user_message: str) -> AIResponse:
        """Generate a complete response via Kimi API."""
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
        )
        content = response.choices[0].message.content or ""
        tokens = response.usage.total_tokens if response.usage else None
        return AIResponse(
            content=content,
            provider=self.name,
            model=self._model,
            tokens_used=tokens,
        )

    async def stream(self, system_prompt: str, user_message: str) -> AsyncIterator[str]:
        """Stream response chunks from Kimi API."""
        stream = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            stream=True,
        )
        async for chunk in stream:
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content

    async def health_check(self) -> bool:
        """Check if the Kimi API is accessible."""
        try:
            response = await self._client.chat.completions.create(
                model=self._model,
                max_tokens=10,
                messages=[{"role": "user", "content": "Hi"}],
            )
            return bool(response.choices)
        except Exception:
            logger.exception("Kimi health check failed")
            return False
