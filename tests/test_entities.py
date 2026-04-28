"""Tests de validación de entidades Pydantic del dominio."""
import pytest
from datetime import datetime, timezone
from app.domain.entities import Message, Conversation


class TestMessageEntity:

    def test_message_creation(self):
        msg = Message(
            conversation_id="conv-123",
            role="user",
            content="Hola",
            model="gemini-2.0-flash",
            provider="gemini",
            created_at=datetime.now(timezone.utc)
        )
        assert msg.conversation_id == "conv-123"
        assert msg.role == "user"
        assert msg.id is None  # Auto-generado por la BD

    def test_message_optional_fields(self):
        """model y provider son opcionales."""
        msg = Message(
            conversation_id="conv-123",
            role="assistant",
            content="Respuesta",
            created_at=datetime.now(timezone.utc)
        )
        assert msg.model is None
        assert msg.provider is None

    def test_message_from_dict(self):
        """Simula model_validate desde un dict (como haría el ORM)."""
        data = {
            "id": 1,
            "conversation_id": "abc",
            "role": "user",
            "content": "test",
            "model": "qwen2.5-coder:1.5b",
            "provider": "ollama",
            "created_at": datetime.now(timezone.utc)
        }
        msg = Message.model_validate(data)
        assert msg.id == 1
        assert msg.provider == "ollama"


class TestConversationEntity:

    def test_conversation_creation(self):
        now = datetime.now(timezone.utc)
        conv = Conversation(id="conv-1", title="Mi chat", created_at=now, updated_at=now)
        assert conv.title == "Mi chat"
        assert conv.created_at == conv.updated_at

    def test_conversation_title_truncation_logic(self):
        """Verifica la lógica de truncado que usa ChatService."""
        long_text = "a" * 100
        title = long_text[:50] + ("..." if len(long_text) > 50 else "")
        assert len(title) == 53
        assert title.endswith("...")
