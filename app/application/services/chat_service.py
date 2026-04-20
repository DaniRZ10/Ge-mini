from typing import List, Optional
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
        # 1. Determinar proveedor e instanciar adaptador
        provider_obj = self.provider_factory.get_provider(model_id)
        provider_name = "gemini" if model_id.startswith("gemini") else "groq"

        # 2. Preparación inicial: Obtener historial previo (vista de solo lectura, fuera de transacción larga)
        history = []
        if conversation_id:
            async with self.session.begin():
                history = await self.msg_repo.get_by_conversation(conversation_id)

        # 3. Obtener respuesta de la IA (Llamada externa, FUERA de la transacción de DB)
        # Pasamos el historial actual. El mensaje nuevo aún no está en la DB.
        reply_content = await provider_obj.send_message(message_content, history, model_id)

        # 4. Una vez tenemos la respuesta, abrimos transacción para guardar TODO de forma atómica
        async with self.session.begin():
            # 4.1 Resolver o crear conversación si es nueva
            if not conversation_id:
                title = message_content[:50] + ("..." if len(message_content) > 50 else "")
                new_conv = Conversation(
                    id=str(uuid.uuid4()),
                    title=title,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
                await self.conv_repo.create(new_conv)
                conversation_id = new_conv.id

            # 4.2 Guardar mensaje del usuario
            user_msg = Message(
                conversation_id=conversation_id,
                role="user",
                content=message_content,
                model=model_id,
                provider=provider_name,
                created_at=datetime.now(timezone.utc)
            )
            await self.msg_repo.add(user_msg)

            # 4.3 Guardar respuesta del asistente
            assistant_msg = Message(
                conversation_id=conversation_id,
                role="assistant",
                content=reply_content,
                model=model_id,
                provider=provider_name,
                created_at=datetime.now(timezone.utc)
            )
            saved_reply = await self.msg_repo.add(assistant_msg)
            
            # 4.4 Actualizar timestamp de la conversación
            await self.conv_repo.touch(conversation_id)

            return saved_reply
