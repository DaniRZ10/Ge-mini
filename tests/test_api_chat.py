"""Tests de integración del endpoint /api/chat."""
import pytest


@pytest.mark.asyncio
async def test_chat_creates_conversation(client):
    """POST /api/chat con mensaje válido debe crear una conversación."""
    payload = {"message": "Hola mundo", "model": "gemini-2.0-flash"}
    response = await client.post("/api/chat", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert "response" in data
    assert "conversation_id" in data
    assert data["conversation_id"] is not None


@pytest.mark.asyncio
async def test_chat_returns_provider(client):
    """La respuesta debe incluir el nombre del proveedor."""
    payload = {"message": "¿Quién eres?", "model": "gemini-2.0-flash"}
    response = await client.post("/api/chat", json=payload)

    data = response.json()
    assert "provider" in data
    assert len(data["provider"]) > 0


@pytest.mark.asyncio
async def test_chat_continues_conversation(client):
    """Enviar 2 mensajes con el mismo conversation_id debe funcionar."""
    # Primer mensaje
    payload1 = {"message": "Mensaje 1", "model": "gemini-2.0-flash"}
    res1 = await client.post("/api/chat", json=payload1)
    conv_id = res1.json()["conversation_id"]

    # Segundo mensaje con el mismo ID
    payload2 = {"message": "Mensaje 2", "model": "gemini-2.0-flash", "conversation_id": conv_id}
    res2 = await client.post("/api/chat", json=payload2)

    assert res2.status_code == 200
    assert res2.json()["conversation_id"] == conv_id


@pytest.mark.asyncio
async def test_chat_empty_message_fails(client):
    """Un payload sin 'message' debe devolver 422."""
    payload = {"model": "gemini-2.0-flash"}
    response = await client.post("/api/chat", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_missing_model_fails(client):
    """Un payload sin 'model' debe devolver 422."""
    payload = {"message": "Hola"}
    response = await client.post("/api/chat", json=payload)
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_chat_response_contains_message_text(client):
    """La respuesta fake debe contener el texto del mensaje original."""
    payload = {"message": "fibonacci", "model": "gemini-2.0-flash"}
    response = await client.post("/api/chat", json=payload)

    data = response.json()
    assert "fibonacci" in data["response"].lower()
