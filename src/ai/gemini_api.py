"""Google Gemini API provider."""

import logging
from typing import AsyncIterator

from google import genai
from google.genai import types

from src.ai.base import AIProvider, AIResponse

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "gemini-2.0-flash"


class GeminiProvider(AIProvider):
    """AI provider using the Google GenAI SDK."""

    def __init__(self, api_key: str, model: str | None = None) -> None:
        self._client = genai.Client(api_key=api_key)
        self._model = model or DEFAULT_MODEL

    @property
    def name(self) -> str:
        return "gemini"

    async def generate(self, system_prompt: str, user_message: str) -> AIResponse:
        """Generate a complete response via Gemini API."""
        response = await self._client.aio.models.generate_content(
            model=self._model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=4096,
            ),
        )
        content = response.text or ""
        tokens = None
        if response.usage_metadata:
            tokens = (
                (response.usage_metadata.prompt_token_count or 0)
                + (response.usage_metadata.candidates_token_count or 0)
            )
        return AIResponse(
            content=content,
            provider=self.name,
            model=self._model,
            tokens_used=tokens,
        )

    async def stream(self, system_prompt: str, user_message: str) -> AsyncIterator[str]:
        """Stream response chunks from Gemini API."""
        async for chunk in await self._client.aio.models.generate_content_stream(
            model=self._model,
            contents=user_message,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=4096,
            ),
        ):
            if chunk.text:
                yield chunk.text

    async def health_check(self) -> bool:
        """Check if the Gemini API is accessible."""
        try:
            response = await self._client.aio.models.generate_content(
                model=self._model,
                contents="Hi",
                config=types.GenerateContentConfig(max_output_tokens=10),
            )
            return bool(response.text)
        except Exception:
            logger.exception("Gemini health check failed")
            return False
