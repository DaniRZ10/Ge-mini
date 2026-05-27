"""Tests para los validadores de claves cloud."""

import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from app.infrastructure.ai.cloud_validators import (
    validate_gemini_key,
    validate_groq_key,
    validate_anthropic_key,
)


@pytest.mark.asyncio
async def test_gemini_empty_key_invalid():
    valid, err = await validate_gemini_key("")
    assert valid is False
    assert "vacía" in err.lower()


@pytest.mark.asyncio
async def test_gemini_bad_format_invalid():
    valid, err = await validate_gemini_key("not-a-real-key")
    assert valid is False
    assert "formato" in err.lower()


@pytest.mark.asyncio
async def test_groq_bad_format_invalid():
    valid, err = await validate_groq_key("AIzaSyABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789")
    assert valid is False
    assert "formato" in err.lower()


@pytest.mark.asyncio
async def test_anthropic_bad_format_invalid():
    valid, err = await validate_anthropic_key("sk-ant-short")
    assert valid is False
    assert "formato" in err.lower()


VALID_GEMINI = "AIzaSy" + "A" * 33
VALID_GROQ = "gsk_" + "A" * 52
VALID_ANTHROPIC = "sk-ant-" + "A" * 80


def _mock_response(status_code: int):
    response = MagicMock()
    response.status_code = status_code
    return response


@pytest.mark.asyncio
async def test_gemini_ping_ok():
    with patch("app.infrastructure.ai.cloud_validators.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=_mock_response(200))
        valid, err = await validate_gemini_key(VALID_GEMINI)
    assert valid is True
    assert err == ""


@pytest.mark.asyncio
async def test_gemini_ping_unauthorized():
    with patch("app.infrastructure.ai.cloud_validators.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=_mock_response(401))
        valid, err = await validate_gemini_key(VALID_GEMINI)
    assert valid is False
    assert "401" in err


@pytest.mark.asyncio
async def test_groq_ping_ok():
    with patch("app.infrastructure.ai.cloud_validators.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=_mock_response(200))
        valid, err = await validate_groq_key(VALID_GROQ)
    assert valid is True


@pytest.mark.asyncio
async def test_anthropic_ping_ok():
    with patch("app.infrastructure.ai.cloud_validators.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(return_value=_mock_response(200))
        valid, err = await validate_anthropic_key(VALID_ANTHROPIC)
    assert valid is True


@pytest.mark.asyncio
async def test_anthropic_network_error():
    with patch("app.infrastructure.ai.cloud_validators.httpx.AsyncClient") as mock_client:
        instance = mock_client.return_value.__aenter__.return_value
        instance.get = AsyncMock(side_effect=Exception("connection refused"))
        valid, err = await validate_anthropic_key(VALID_ANTHROPIC)
    assert valid is False
    assert "red" in err.lower() or "error" in err.lower()
