"""
Tests for GET /api/models/local/status — local model availability endpoint.
Mocks get_ollama_installed_models to isolate from Ollama runtime.
"""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.infrastructure.ai.factory import KNOWN_LOCAL_MODELS

ALL_TAGS = [m["tag"] for m in KNOWN_LOCAL_MODELS]


@pytest.mark.asyncio
async def test_local_status_ollama_running_with_models():
    """Ollama up with two models installed → both appear in 'available'."""
    installed = ["qwen2.5-coder:1.5b", "mistral:7b-instruct-q4_K_M"]

    with patch(
        "app.main.get_ollama_installed_models",
        new=AsyncMock(return_value=(installed, True)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/models/local/status")

    assert response.status_code == 200
    body = response.json()
    assert body["ollama_running"] is True
    assert set(body["available"]) == set(installed)
    assert set(body["all"]) == set(ALL_TAGS)


@pytest.mark.asyncio
async def test_local_status_ollama_running_no_models():
    """Ollama up but no local models downloaded yet → available is empty."""
    with patch(
        "app.main.get_ollama_installed_models",
        new=AsyncMock(return_value=([], True)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/models/local/status")

    assert response.status_code == 200
    body = response.json()
    assert body["ollama_running"] is True
    assert body["available"] == []
    assert set(body["all"]) == set(ALL_TAGS)


@pytest.mark.asyncio
async def test_local_status_ollama_down():
    """Ollama not running → HTTP 200 with empty available and ollama_running=False."""
    with patch(
        "app.main.get_ollama_installed_models",
        new=AsyncMock(return_value=([], False)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/models/local/status")

    assert response.status_code == 200
    body = response.json()
    assert body["ollama_running"] is False
    assert body["available"] == []
    assert set(body["all"]) == set(ALL_TAGS)


@pytest.mark.asyncio
async def test_local_status_returns_only_known_models():
    """
    Ollama may have extra models (e.g. user-pulled manually).
    'available' only lists models that are in KNOWN_LOCAL_MODELS and also installed.
    'all' always contains exactly the 5 known tags.
    """
    installed = ["qwen2.5-coder:3b", "some-random-model:latest"]

    with patch(
        "app.main.get_ollama_installed_models",
        new=AsyncMock(return_value=(installed, True)),
    ):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            response = await client.get("/api/models/local/status")

    body = response.json()
    assert "some-random-model:latest" not in body["available"]
    assert "qwen2.5-coder:3b" in body["available"]
    assert len(body["all"]) == len(KNOWN_LOCAL_MODELS)
