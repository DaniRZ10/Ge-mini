import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.mark.asyncio
async def test_read_root(client):
    """Verifica que el endpoint root responda correctamente."""
    response = await client.get("/")
    assert response.status_code == 200
    assert "Ge-mini is alive" in response.json()["status"]

@pytest.mark.asyncio
async def test_create_and_chat_gemini(client):
    """Prueba el flujo completo con Gemini (usando Mock)."""
    payload = {
        "message": "Hola, ¿quién eres?",
        "model": "gemini-1.5-flash"
    }
    response = await client.post("/api/chat", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "soy tu ge-mini de prueba" in data["response"].lower()
    assert data["provider"] == "gemini"
    assert "conversation_id" in data

@pytest.mark.asyncio
async def test_chat_groq_mock(client):
    """Prueba que el ruteo a Groq funciona y devuelve la respuesta simulada."""
    payload = {
        "message": "Dime algo en Llama",
        "model": "llama-3.3-70b-versatile"
    }
    response = await client.post("/api/chat", json=payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "simulada de llama" in data["response"].lower()
    assert data["provider"] == "groq"

