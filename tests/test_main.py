"""Tests del endpoint raíz y health check."""
import pytest


@pytest.mark.asyncio
async def test_read_root(client):
    """Verifica que el endpoint root responda correctamente."""
    response = await client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "Ge-mini is alive" in data["status"]
    assert "providers" in data


@pytest.mark.asyncio
async def test_static_files_accessible(client):
    """Verifica que los archivos estáticos se sirven correctamente."""
    response = await client.get("/static/index.html")
    assert response.status_code == 200
    assert "Ge-mini" in response.text
