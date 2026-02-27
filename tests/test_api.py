"""Test all REST API endpoints."""

import os
from unittest.mock import patch, AsyncMock

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from src.api.server import create_app


@pytest_asyncio.fixture
async def client(tmp_path):
    """Create a test client with a temporary database."""
    db_path = str(tmp_path / "test_api.db")

    # Patch the config and DB path
    test_config = {
        "app": {"name": "DeutschLerner", "version": "1.0.0", "log_level": "WARNING"},
        "server": {"host": "0.0.0.0", "port": 8000, "api_key": ""},
        "ai": {"default_provider": "claude_cli", "default_model": None},
        "database": {"path": db_path},
        "heartbeat": {"enabled": False},
        "learning": {"difficulty": "A2"},
    }

    with patch("src.api.dependencies._config", test_config), \
         patch("src.api.dependencies.get_db_path", return_value=db_path):
        app = create_app()
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    response = await client.get("/api/v1/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "ok"


@pytest.mark.asyncio
async def test_app_info(client: AsyncClient) -> None:
    response = await client.get("/api/v1/info")
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "DeutschLerner"


@pytest.mark.asyncio
async def test_list_vocabulary_empty(client: AsyncClient) -> None:
    response = await client.get("/api/v1/vocabulary")
    assert response.status_code == 200
    data = response.json()
    assert data["items"] == []
    assert data["total"] == 0


@pytest.mark.asyncio
async def test_create_vocabulary(client: AsyncClient) -> None:
    response = await client.post("/api/v1/vocabulary", json={
        "german": "Hund",
        "chinese": "狗",
        "gender": "der",
        "part_of_speech": "noun",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["german"] == "Hund"
    assert data["status"] == "unknown"


@pytest.mark.asyncio
async def test_create_and_list_vocabulary(client: AsyncClient) -> None:
    await client.post("/api/v1/vocabulary", json={"german": "Katze", "chinese": "猫"})
    response = await client.get("/api/v1/vocabulary")
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["german"] == "Katze"


@pytest.mark.asyncio
async def test_update_vocabulary_status(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/vocabulary", json={"german": "Baum", "chinese": "树"})
    vocab_id = create_resp.json()["id"]

    response = await client.patch(f"/api/v1/vocabulary/{vocab_id}", json={"status": "known"})
    assert response.status_code == 200
    assert response.json()["updated"] is True


@pytest.mark.asyncio
async def test_delete_vocabulary(client: AsyncClient) -> None:
    create_resp = await client.post("/api/v1/vocabulary", json={"german": "Stuhl", "chinese": "椅子"})
    vocab_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/vocabulary/{vocab_id}")
    assert response.status_code == 200
    assert response.json()["deleted"] is True


@pytest.mark.asyncio
async def test_vocabulary_stats(client: AsyncClient) -> None:
    await client.post("/api/v1/vocabulary", json={"german": "Tisch", "chinese": "桌子"})
    response = await client.get("/api/v1/vocabulary/stats")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["unknown"] == 1


@pytest.mark.asyncio
async def test_create_sentence(client: AsyncClient) -> None:
    response = await client.post("/api/v1/sentences", json={
        "german": "Das ist ein Hund.",
        "chinese": "这是一只狗。",
    })
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_list_sentences(client: AsyncClient) -> None:
    await client.post("/api/v1/sentences", json={
        "german": "Der Hund ist groß.",
        "chinese": "这只狗很大。",
    })
    response = await client.get("/api/v1/sentences")
    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_memory_stats(client: AsyncClient) -> None:
    response = await client.get("/api/v1/memory/stats")
    assert response.status_code == 200
    data = response.json()
    assert "vocabulary" in data
    assert "sentences" in data


@pytest.mark.asyncio
async def test_memory_export(client: AsyncClient) -> None:
    response = await client.get("/api/v1/memory/export")
    assert response.status_code == 200
    data = response.json()
    assert "vocabulary" in data
    assert "sentences" in data


@pytest.mark.asyncio
async def test_list_providers(client: AsyncClient) -> None:
    response = await client.get("/api/v1/providers")
    assert response.status_code == 200
    data = response.json()
    assert len(data["providers"]) > 0


@pytest.mark.asyncio
async def test_get_current_provider(client: AsyncClient) -> None:
    response = await client.get("/api/v1/provider/current")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_heartbeat_status(client: AsyncClient) -> None:
    response = await client.get("/api/v1/heartbeat/status")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_heartbeat_history(client: AsyncClient) -> None:
    response = await client.get("/api/v1/heartbeat/history")
    assert response.status_code == 200
    assert "items" in response.json()
