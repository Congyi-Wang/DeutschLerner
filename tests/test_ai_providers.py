"""Test AI provider interface compliance."""

import pytest

from src.ai.base import AIResponse
from tests.conftest import MockProvider


@pytest.fixture
def provider() -> MockProvider:
    return MockProvider()


@pytest.mark.asyncio
async def test_mock_provider_name(provider: MockProvider) -> None:
    assert provider.name == "mock"


@pytest.mark.asyncio
async def test_mock_provider_generate(provider: MockProvider) -> None:
    response = await provider.generate("system", "user message")
    assert isinstance(response, AIResponse)
    assert response.provider == "mock"
    assert response.model == "mock-v1"
    assert "Supermarkt" in response.content


@pytest.mark.asyncio
async def test_mock_provider_stream(provider: MockProvider) -> None:
    chunks = []
    async for chunk in provider.stream("system", "user message"):
        chunks.append(chunk)
    assert len(chunks) > 0
    full = "".join(chunks)
    assert "Supermarkt" in full


@pytest.mark.asyncio
async def test_mock_provider_health(provider: MockProvider) -> None:
    assert await provider.health_check() is True
