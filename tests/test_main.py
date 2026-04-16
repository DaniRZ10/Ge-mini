import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_read_root():
    """Verifica que el endpoint root responda correctamente."""
    # En httpx >= 0.28.0 se usa transport para montar la app de FastAPI
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/")
    
    assert response.status_code == 200
    assert "Ge-mini is alive" in response.json()["status"]
