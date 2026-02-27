"""Abstract base class for all AI providers."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import AsyncIterator


@dataclass
class AIResponse:
    """Structured response from an AI provider."""

    content: str
    provider: str
    model: str
    tokens_used: int | None = None
    raw_response: dict | None = field(default=None, repr=False)


class AIProvider(ABC):
    """Base class for all AI providers."""

    @property
    @abstractmethod
    def name(self) -> str:
        """Provider name: 'claude', 'openai', 'gemini', 'kimi', 'deepseek', 'claude_cli'."""
        ...

    @abstractmethod
    async def generate(self, system_prompt: str, user_message: str) -> AIResponse:
        """Generate a complete response."""
        ...

    @abstractmethod
    async def stream(self, system_prompt: str, user_message: str) -> AsyncIterator[str]:
        """Stream response chunks for CLI mode."""
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the provider is accessible."""
        ...
