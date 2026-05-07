import pytest
import os
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from app.main import app
from app.api.dependencies import require_token

client = TestClient(app)

@pytest.fixture
def mock_app_token():
    with patch("app.api.dependencies.APP_TOKEN", "test-token"):
        yield "test-token"

def test_auth_unauthorized_when_token_set(mock_app_token):
    # Sin token
    response = client.get("/api/conversations")
    assert response.status_code == 401
    assert response.json()["detail"] == "Unauthorized"

def test_auth_authorized_when_token_set(mock_app_token):
    # Con token correcto
    response = client.get("/api/conversations", headers={"Authorization": f"Bearer {mock_app_token}"})
    # Aquí puede fallar por DB u otra cosa, pero no debería ser 401
    assert response.status_code != 401

@pytest.mark.asyncio
async def test_chat_service_persists_user_message_before_ai_call():
    from app.application.services.chat_service import ChatService
    
    # Mock repos y factory
    from unittest.mock import MagicMock
    session = MagicMock()
    # Mock para el context manager async with self.session.begin()
    class AsyncCM:
        async def __aenter__(self): return None
        async def __aexit__(self, *args): return None
    
    session.begin.return_value = AsyncCM()
    
    conv_repo = MagicMock()
    conv_repo.create = AsyncMock()
    conv_repo.touch = AsyncMock()
    msg_repo = MagicMock()
    msg_repo.add = AsyncMock()
    msg_repo.get_by_conversation = AsyncMock()
    
    factory = MagicMock()
    provider = MagicMock()
    provider.send_message = AsyncMock()
    
    factory.get_provider.return_value = provider
    # Simulamos fallo en el proveedor
    provider.send_message.side_effect = Exception("AI Crash")
    
    service = ChatService(session, conv_repo, msg_repo, factory)
    
    # Intentamos chat
    with pytest.raises(Exception, match="AI Crash"):
        await service.start_chat("Hola", "gemini-pro")
    
    # Verificamos que se intentó guardar el mensaje del usuario
    # msg_repo.add debería haberse llamado para el rol "user"
    assert msg_repo.add.called
    calls = msg_repo.add.call_args_list
    user_msg_call = any(call.args[0].role == "user" for call in calls)
    assert user_msg_call, "El mensaje del usuario debería haberse persistido antes del fallo de la IA"

def test_marked_parse_usage_in_frontend():
    # Esta prueba es estática: leemos el archivo y verificamos la llamada
    with open("static/index.html", "r", encoding="utf-8") as f:
        content = f.read()
        assert "DOMPurify.sanitize(marked.parse(" in content
        # Debería haber al menos 2 ocurrencias (según mi cambio)
        assert content.count("DOMPurify.sanitize(marked.parse(") >= 2
