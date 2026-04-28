"""Tests del endpoint de streaming /api/chat/stream."""
import pytest


@pytest.mark.asyncio
async def test_stream_returns_200(client):
    """POST /api/chat/stream debe devolver 200."""
    payload = {"message": "Hola streaming", "model": "gemini-2.0-flash"}
    response = await client.post("/api/chat/stream", json=payload)
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_stream_returns_conversation_id_header(client):
    """La respuesta debe incluir el header X-Conversation-Id."""
    payload = {"message": "Test header", "model": "gemini-2.0-flash"}
    response = await client.post("/api/chat/stream", json=payload)
    
    assert response.status_code == 200
    conv_id = response.headers.get("x-conversation-id")
    assert conv_id is not None
    assert len(conv_id) > 0


@pytest.mark.asyncio
async def test_stream_returns_text_content(client):
    """La respuesta de streaming debe contener texto del FakeProvider."""
    payload = {"message": "fibonacci", "model": "gemini-2.0-flash"}
    response = await client.post("/api/chat/stream", json=payload)

    text = response.text
    assert len(text) > 0
    # El FakeProvider devuelve "Streaming fake para: {message}"
    assert "fibonacci" in text.lower()


@pytest.mark.asyncio
async def test_stream_with_existing_conversation(client):
    """Streaming con un conversation_id existente debe funcionar."""
    # Crear conversación primero
    chat_res = await client.post("/api/chat", json={"message": "Setup", "model": "gemini-2.0-flash"})
    conv_id = chat_res.json()["conversation_id"]

    # Ahora usar streaming con ese ID
    payload = {"message": "Continuar", "model": "gemini-2.0-flash", "conversation_id": conv_id}
    response = await client.post("/api/chat/stream", json=payload)
    
    assert response.status_code == 200
    assert response.headers.get("x-conversation-id") == conv_id
