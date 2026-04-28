"""Tests del CRUD de conversaciones."""
import pytest


@pytest.mark.asyncio
async def test_list_conversations_empty(client):
    """Sin datos, debe devolver una lista vacía."""
    response = await client.get("/api/conversations")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_list_conversations_after_chat(client):
    """Tras chatear, la conversación debe aparecer en la lista."""
    # Crear una conversación vía chat
    await client.post("/api/chat", json={"message": "Hola", "model": "gemini-2.0-flash"})

    response = await client.get("/api/conversations")
    assert response.status_code == 200
    convs = response.json()
    assert len(convs) >= 1
    assert "Hola" in convs[0]["title"]


@pytest.mark.asyncio
async def test_get_messages_for_conversation(client):
    """GET /api/conversations/{id}/messages debe devolver los mensajes."""
    # Crear una conversación
    chat_res = await client.post("/api/chat", json={"message": "Test mensajes", "model": "gemini-2.0-flash"})
    conv_id = chat_res.json()["conversation_id"]

    # Obtener los mensajes
    response = await client.get(f"/api/conversations/{conv_id}/messages")
    assert response.status_code == 200
    messages = response.json()
    # Debe haber al menos 2 mensajes: el del usuario y la respuesta
    assert len(messages) >= 2
    assert messages[0]["role"] == "user"
    assert messages[1]["role"] == "assistant"


@pytest.mark.asyncio
async def test_get_messages_nonexistent_conversation(client):
    """Pedir mensajes de una conversación inexistente devuelve lista vacía."""
    response = await client.get("/api/conversations/id-que-no-existe/messages")
    assert response.status_code == 200
    assert response.json() == []


@pytest.mark.asyncio
async def test_delete_conversation(client):
    """DELETE debe eliminar la conversación y ya no aparecer en la lista."""
    # Crear una conversación
    chat_res = await client.post("/api/chat", json={"message": "Para borrar", "model": "gemini-2.0-flash"})
    conv_id = chat_res.json()["conversation_id"]

    # Borrar
    del_response = await client.delete(f"/api/conversations/{conv_id}")
    assert del_response.status_code == 200

    # Verificar que ya no está
    list_response = await client.get("/api/conversations")
    conv_ids = [c["id"] for c in list_response.json()]
    assert conv_id not in conv_ids


@pytest.mark.asyncio
async def test_delete_nonexistent_returns_404(client):
    """Borrar una conversación que no existe debe devolver 404."""
    response = await client.delete("/api/conversations/fake-id-12345")
    assert response.status_code == 404
