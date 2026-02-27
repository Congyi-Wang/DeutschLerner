"""Claude Code CLI subprocess provider — NO API key needed."""

import asyncio
import logging
import shutil
from typing import AsyncIterator

from src.ai.base import AIProvider, AIResponse

logger = logging.getLogger(__name__)


class ClaudeCLIProvider(AIProvider):
    """Uses the locally installed Claude Code CLI binary."""

    def __init__(self, binary_path: str | None = None) -> None:
        self._binary = binary_path or shutil.which("claude") or "claude"

    @property
    def name(self) -> str:
        return "claude_cli"

    async def generate(self, system_prompt: str, user_message: str) -> AIResponse:
        """Generate a complete response by calling the claude CLI."""
        full_prompt = f"{system_prompt}\n\n{user_message}"
        proc = await asyncio.create_subprocess_exec(
            self._binary, "-p", full_prompt, "--output-format", "text",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await proc.communicate()
        if proc.returncode != 0:
            raise RuntimeError(f"Claude CLI error (exit {proc.returncode}): {stderr.decode()}")
        return AIResponse(
            content=stdout.decode().strip(),
            provider="claude_cli",
            model="claude-code",
        )

    async def stream(self, system_prompt: str, user_message: str) -> AsyncIterator[str]:
        """Stream response from claude CLI — reads stdout line by line."""
        full_prompt = f"{system_prompt}\n\n{user_message}"
        proc = await asyncio.create_subprocess_exec(
            self._binary, "-p", full_prompt, "--output-format", "text",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        assert proc.stdout is not None
        while True:
            chunk = await proc.stdout.read(256)
            if not chunk:
                break
            yield chunk.decode()
        await proc.wait()

    async def health_check(self) -> bool:
        """Check if the claude binary is available."""
        try:
            proc = await asyncio.create_subprocess_exec(
                self._binary, "--version",
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
            )
            await proc.communicate()
            return proc.returncode == 0
        except FileNotFoundError:
            logger.warning("Claude CLI binary not found at '%s'", self._binary)
            return False
        except Exception:
            logger.exception("Claude CLI health check failed")
            return False
