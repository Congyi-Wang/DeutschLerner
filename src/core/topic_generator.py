"""Topic generation with AI response parsing."""

import json
import logging
import re
from dataclasses import dataclass, field
from pathlib import Path

from src.ai.base import AIProvider, AIResponse

logger = logging.getLogger(__name__)

PROMPTS_DIR = Path(__file__).resolve().parent.parent.parent / "prompts"


@dataclass
class TopicResult:
    """Parsed result of a generated topic."""

    topic_title_de: str = ""
    topic_title_cn: str = ""
    summary_cn: str = ""
    vocabulary: list[dict] = field(default_factory=list)
    sentences: list[dict] = field(default_factory=list)
    grammar_tips: str = ""
    exercise: str = ""
    raw_content: str = ""
    provider: str = ""
    model: str = ""


def _load_prompt(filename: str) -> str:
    """Load a prompt template from the prompts directory."""
    path = PROMPTS_DIR / filename
    return path.read_text(encoding="utf-8")


def _extract_json(text: str) -> dict:
    """Extract JSON from AI response, stripping markdown code fences if present."""
    # Try to find JSON in code fences first
    match = re.search(r"```(?:json)?\s*\n?(.*?)\n?\s*```", text, re.DOTALL)
    if match:
        text = match.group(1)

    # Strip leading/trailing whitespace
    text = text.strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        # Try to find the first { ... } block
        brace_match = re.search(r"\{.*\}", text, re.DOTALL)
        if brace_match:
            try:
                return json.loads(brace_match.group(0))
            except json.JSONDecodeError:
                pass
        logger.error("Failed to parse JSON from AI response")
        return {}


class TopicGenerator:
    """Generates structured German learning topics via AI."""

    def __init__(self, ai_provider: AIProvider) -> None:
        self.ai = ai_provider

    async def generate_topic(
        self, user_input: str, memory_context: str = ""
    ) -> TopicResult:
        """Generate a learning topic from user input.

        Args:
            user_input: What the user wants to learn about.
            memory_context: Context about what the user already knows.

        Returns:
            A structured TopicResult with vocabulary, sentences, etc.
        """
        system_prompt = _load_prompt("topic_generation.md")
        if memory_context:
            system_prompt += f"\n\n## 用户学习记录\n{memory_context}"

        response = await self.ai.generate(system_prompt, user_input)
        return self._parse_response(response)

    async def generate_heartbeat_topic(self, category: str) -> TopicResult:
        """Generate a heartbeat topic for a given category.

        Args:
            category: The topic category (e.g. 'daily_life', 'grammar').

        Returns:
            A structured TopicResult.
        """
        system_prompt = _load_prompt("heartbeat_topic.md").replace("{category}", category)
        user_message = f"请生成一个关于「{category}」类别的德语学习内容。"
        response = await self.ai.generate(system_prompt, user_message)
        return self._parse_response(response)

    def _parse_response(self, response: AIResponse) -> TopicResult:
        """Parse an AI response into a structured TopicResult."""
        data = _extract_json(response.content)

        if not data:
            logger.warning("Could not parse structured data from AI response")
            return TopicResult(
                raw_content=response.content,
                provider=response.provider,
                model=response.model,
            )

        return TopicResult(
            topic_title_de=data.get("topic_title_de", ""),
            topic_title_cn=data.get("topic_title_cn", ""),
            summary_cn=data.get("summary_cn", ""),
            vocabulary=data.get("vocabulary", []),
            sentences=data.get("sentences", []),
            grammar_tips=data.get("grammar_tips", ""),
            exercise=data.get("exercise", ""),
            raw_content=response.content,
            provider=response.provider,
            model=response.model,
        )
