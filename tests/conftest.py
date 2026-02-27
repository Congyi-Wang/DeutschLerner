"""Shared fixtures for DeutschLerner tests."""

import asyncio
import os
from typing import AsyncIterator
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from src.ai.base import AIProvider, AIResponse
from src.storage.models import Base
from src.storage.repository import Repository


class MockProvider(AIProvider):
    """Mock AI provider that returns canned responses."""

    MOCK_RESPONSE = """{
  "topic_title_de": "Im Supermarkt einkaufen",
  "topic_title_cn": "在超市购物",
  "summary_cn": "学习在德国超市购物时常用的词汇和表达。",
  "vocabulary": [
    {
      "german": "der Einkaufswagen",
      "chinese": "购物车",
      "gender": "der",
      "part_of_speech": "noun",
      "example_de": "Ich nehme einen Einkaufswagen.",
      "example_cn": "我拿一辆购物车。"
    },
    {
      "german": "die Kasse",
      "chinese": "收银台",
      "gender": "die",
      "part_of_speech": "noun",
      "example_de": "Bitte gehen Sie zur Kasse.",
      "example_cn": "请去收银台。"
    },
    {
      "german": "bezahlen",
      "chinese": "付款",
      "gender": null,
      "part_of_speech": "verb",
      "example_de": "Ich möchte mit Karte bezahlen.",
      "example_cn": "我想用卡付款。"
    }
  ],
  "sentences": [
    {
      "german": "Wo finde ich die Milch?",
      "chinese": "牛奶在哪里？",
      "grammar_note": "Wo + 动词 + 主语 + 宾语：用于询问位置"
    },
    {
      "german": "Das kostet drei Euro fünfzig.",
      "chinese": "这个三欧元五十。",
      "grammar_note": "价格表达：数字 + Euro + 数字"
    }
  ],
  "grammar_tips": "德语中，名词的冠词（der/die/das）必须记住，因为它们决定了形容词和代词的变化形式。",
  "exercise": "请用德语说：我想买两公斤苹果。(提示：kaufen, zwei Kilo, der Apfel)"
}"""

    @property
    def name(self) -> str:
        return "mock"

    async def generate(self, system_prompt: str, user_message: str) -> AIResponse:
        return AIResponse(
            content=self.MOCK_RESPONSE,
            provider="mock",
            model="mock-v1",
            tokens_used=100,
        )

    async def stream(self, system_prompt: str, user_message: str) -> AsyncIterator[str]:
        for chunk in self.MOCK_RESPONSE.split(" "):
            yield chunk + " "

    async def health_check(self) -> bool:
        return True


@pytest.fixture
def mock_provider() -> MockProvider:
    """Provide a mock AI provider."""
    return MockProvider()


@pytest_asyncio.fixture
async def db_session(tmp_path) -> AsyncIterator[AsyncSession]:
    """Provide a fresh in-memory database session for each test."""
    db_path = str(tmp_path / "test.db")
    engine = create_async_engine(f"sqlite+aiosqlite:///{db_path}", echo=False)

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    factory = async_sessionmaker(engine, expire_on_commit=False)
    session = factory()

    yield session

    await session.close()
    await engine.dispose()


@pytest_asyncio.fixture
async def repo(db_session: AsyncSession) -> Repository:
    """Provide a Repository backed by the test database."""
    return Repository(db_session)
