"""Tests unitarios del ChatService."""
import pytest
from datetime import datetime, timezone
from app.application.services.chat_service import ChatService
from app.infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from tests.conftest import FakeProviderFactory


@pytest.mark.asyncio
async def test_start_chat_creates_new_conversation(db_session):
    """Sin conversation_id, el servicio debe crear una conversación nueva."""
    conv_repo = SqlAlchemyConversationRepository(db_session)
    msg_repo = SqlAlchemyMessageRepository(db_session)
    factory = FakeProviderFactory()
    service = ChatService(db_session, conv_repo, msg_repo, factory)

    reply = await service.start_chat(
        message_content="Hola",
        model_id="gemini-2.0-flash",
        conversation_id=None
    )

    assert reply.role == "assistant"
    assert reply.conversation_id is not None
    assert "Hola" in reply.content


@pytest.mark.asyncio
async def test_start_chat_reuses_conversation(db_session):
    """Con conversation_id, el servicio debe reutilizar la conversación."""
    conv_repo = SqlAlchemyConversationRepository(db_session)
    msg_repo = SqlAlchemyMessageRepository(db_session)
    factory = FakeProviderFactory()
    service = ChatService(db_session, conv_repo, msg_repo, factory)

    # Crear primera conversación
    reply1 = await service.start_chat("Primer mensaje", "gemini-2.0-flash", None)
    conv_id = reply1.conversation_id

    # Reutilizar la misma conversación
    reply2 = await service.start_chat("Segundo mensaje", "gemini-2.0-flash", conv_id)
    assert reply2.conversation_id == conv_id


@pytest.mark.asyncio
async def test_provider_routing_via_factory():
    """Verifica que la fábrica enruta y los providers devuelven el nombre correcto."""
    from app.infrastructure.ai.factory import AiProviderFactory
    import os
    from unittest.mock import patch

    with patch.dict(os.environ, {"GEMINI_API_KEY": "fake", "GROQ_API_KEY": "fake"}):
        factory = AiProviderFactory(system_prompt="test")
        
        # Caso Gemini
        assert factory.get_provider("gemini-2.0-flash").name == "gemini"
        # Caso Ollama (local)
        assert factory.get_provider("qwen2.5-coder:1.5b").name == "ollama"
        # Caso Groq
        assert factory.get_provider("llama-3.3-70b-versatile").name == "groq"


@pytest.mark.asyncio
async def test_stream_generator_yields_chunks(db_session):
    """El generador de streaming debe emitir chunks de texto."""
    conv_repo = SqlAlchemyConversationRepository(db_session)
    msg_repo = SqlAlchemyMessageRepository(db_session)
    factory = FakeProviderFactory()
    service = ChatService(db_session, conv_repo, msg_repo, factory)

    chunks = []
    async for chunk in service.get_stream_generator("test", "gemini-2.0-flash", None):
        chunks.append(chunk)

    assert len(chunks) > 0
    full_text = "".join(chunks)
    assert "test" in full_text.lower()
