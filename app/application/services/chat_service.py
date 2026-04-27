from typing import List, Optional, AsyncIterator
from datetime import datetime, timezone
import uuid

from sqlalchemy.ext.asyncio import AsyncSession
from ...domain.entities import Conversation, Message
from ...infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from ...infrastructure.ai.factory import AiProviderFactory

class ChatService:
    def __init__(
        self,
        session: AsyncSession,
        conv_repo: SqlAlchemyConversationRepository,
        msg_repo: SqlAlchemyMessageRepository,
        provider_factory: AiProviderFactory
    ):
        self.session = session
        self.conv_repo = conv_repo
        self.msg_repo = msg_repo
        self.provider_factory = provider_factory

    async def start_chat(self, message_content: str, model_id: str, conversation_id: Optional[str] = None) -> Message:
        provider_obj = self.provider_factory.get_provider(model_id)
        provider_name = self._get_provider_name(model_id)

        history = []
        if conversation_id:
            async with self.session.begin():
                history = await self.msg_repo.get_by_conversation(conversation_id)

        reply_content = await provider_obj.send_message(message_content, history, model_id)

        async with self.session.begin():
            if not conversation_id:
                conversation_id = await self._create_conversation(message_content)

            await self._save_message(conversation_id, "user", message_content, model_id, provider_name)
            saved_reply = await self._save_message(conversation_id, "assistant", reply_content, model_id, provider_name)
            await self.conv_repo.touch(conversation_id)

            return saved_reply

    async def start_chat_stream(self, message_content: str, model_id: str, conversation_id: Optional[str] = None) -> AsyncIterator[str]:
        provider_obj = self.provider_factory.get_provider(model_id)
        provider_name = self._get_provider_name(model_id)

        history = []
        if conversation_id:
            # Usamos una sesión rápida para el historial
            async with self.session.begin():
                history = await self.msg_repo.get_by_conversation(conversation_id)

        full_reply = ""
        
        # Primero enviamos el ID de conversación al frontend si es nueva
        # (Esto se manejará mejor en el endpoint, aquí solo devolvemos el texto)
        
        async for chunk in provider_obj.send_message_stream(message_content, history, model_id):
            full_reply += chunk
            yield chunk

        # Al terminar el stream, guardamos en la base de datos
        # IMPORTANTE: Necesitamos una nueva transacción
        async with self.session.begin():
            if not conversation_id:
                conversation_id = await self._create_conversation(message_content)
                # OJO: El frontend necesita saber este ID. 
                # En una implementación real de SSE se enviaría un evento especial.
            
            await self._save_message(conversation_id, "user", message_content, model_id, provider_name)
            await self._save_message(conversation_id, "assistant", full_reply, model_id, provider_name)
            await self.conv_repo.touch(conversation_id)

    def _get_provider_name(self, model_id: str) -> str:
        if model_id.startswith("gemini"): return "gemini"
        if any(m in model_id.lower() for m in ["qwen", "deepseek", "phi", "gemma"]): return "ollama"
        return "groq"

    async def _create_conversation(self, message_content: str) -> str:
        title = message_content[:50] + ("..." if len(message_content) > 50 else "")
        new_conv = Conversation(
            id=str(uuid.uuid4()),
            title=title,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        await self.conv_repo.create(new_conv)
        return new_conv.id

    async def _save_message(self, conversation_id: str, role: str, content: str, model: str, provider: str) -> Message:
        msg = Message(
            conversation_id=conversation_id,
            role=role,
            content=content,
            model=model,
            provider=provider,
            created_at=datetime.now(timezone.utc)
        )
        return await self.msg_repo.add(msg)
