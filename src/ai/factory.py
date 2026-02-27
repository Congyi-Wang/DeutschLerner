"""Provider factory — create AI provider by name string."""

import os
import logging

from src.ai.base import AIProvider

logger = logging.getLogger(__name__)

_PROVIDER_REGISTRY: dict[str, type] = {}


def _ensure_registry() -> None:
    """Lazily populate the registry to avoid import-time side effects."""
    if _PROVIDER_REGISTRY:
        return

    from src.ai.claude_api import ClaudeProvider
    from src.ai.openai_api import OpenAIProvider
    from src.ai.gemini_api import GeminiProvider
    from src.ai.kimi_api import KimiProvider
    from src.ai.deepseek_api import DeepSeekProvider
    from src.ai.claude_cli import ClaudeCLIProvider

    _PROVIDER_REGISTRY.update({
        "claude": ClaudeProvider,
        "openai": OpenAIProvider,
        "gemini": GeminiProvider,
        "kimi": KimiProvider,
        "deepseek": DeepSeekProvider,
        "claude_cli": ClaudeCLIProvider,
    })


# Maps provider name → environment variable for the API key
_KEY_ENV_MAP: dict[str, str] = {
    "claude": "ANTHROPIC_API_KEY",
    "openai": "OPENAI_API_KEY",
    "gemini": "GOOGLE_API_KEY",
    "kimi": "KIMI_API_KEY",
    "deepseek": "DEEPSEEK_API_KEY",
}


def create_provider(name: str, model: str | None = None) -> AIProvider:
    """Create an AI provider instance by name.

    Args:
        name: Provider name (claude, openai, gemini, kimi, deepseek, claude_cli).
        model: Optional model override.

    Returns:
        An initialized AIProvider instance.

    Raises:
        ValueError: If the provider name is unknown.
        RuntimeError: If the required API key is missing.
    """
    _ensure_registry()

    if name not in _PROVIDER_REGISTRY:
        available = ", ".join(sorted(_PROVIDER_REGISTRY.keys()))
        raise ValueError(f"Unknown provider '{name}'. Available: {available}")

    if name == "claude_cli":
        return _PROVIDER_REGISTRY[name]()

    env_var = _KEY_ENV_MAP.get(name, "")
    api_key = os.environ.get(env_var, "")
    if not api_key:
        raise RuntimeError(
            f"API key for '{name}' not found. Set the {env_var} environment variable."
        )

    kwargs: dict[str, str] = {"api_key": api_key}
    if model:
        kwargs["model"] = model

    return _PROVIDER_REGISTRY[name](**kwargs)


def list_providers() -> list[dict[str, str]]:
    """List all available providers and their configuration status."""
    _ensure_registry()
    result = []
    for name in sorted(_PROVIDER_REGISTRY.keys()):
        env_var = _KEY_ENV_MAP.get(name, "")
        configured = bool(os.environ.get(env_var)) if env_var else True
        result.append({
            "name": name,
            "env_var": env_var or "(none — uses local CLI)",
            "configured": "yes" if configured else "no",
        })
    return result
