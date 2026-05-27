"""Tests para GET /api/models/cloud/status."""

import pytest
from unittest.mock import patch, AsyncMock
from httpx import AsyncClient, ASGITransport
from app.main import app


@pytest.mark.asyncio
async def test_cloud_status_none_configured(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    # Limpia cache
    from app.main import _cloud_status_cache
    _cloud_status_cache.clear()

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        r = await client.get("/api/models/cloud/status")

    assert r.status_code == 200
    body = r.json()
    for p in ("gemini", "groq", "anthropic"):
        assert body[p]["configured"] is False
        assert body[p]["valid"] is False


@pytest.mark.asyncio
async def test_cloud_status_all_valid(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy" + "A" * 33)
    monkeypatch.setenv("GROQ_API_KEY", "gsk_" + "A" * 52)
    monkeypatch.setenv("ANTHROPIC_API_KEY", "sk-ant-" + "A" * 80)
    from app.main import _cloud_status_cache
    _cloud_status_cache.clear()

    with patch("app.main.validate_gemini_key", new=AsyncMock(return_value=(True, ""))), \
         patch("app.main.validate_groq_key", new=AsyncMock(return_value=(True, ""))), \
         patch("app.main.validate_anthropic_key", new=AsyncMock(return_value=(True, ""))):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/models/cloud/status")

    body = r.json()
    for p in ("gemini", "groq", "anthropic"):
        assert body[p]["configured"] is True
        assert body[p]["valid"] is True


@pytest.mark.asyncio
async def test_cloud_status_configured_but_invalid(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "AIzaSy" + "A" * 33)
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    from app.main import _cloud_status_cache
    _cloud_status_cache.clear()

    with patch("app.main.validate_gemini_key", new=AsyncMock(return_value=(False, "HTTP 401"))):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
            r = await client.get("/api/models/cloud/status")

    body = r.json()
    assert body["gemini"]["configured"] is True
    assert body["gemini"]["valid"] is False
    assert body["gemini"]["error"] == "HTTP 401"
    assert body["groq"]["configured"] is False
