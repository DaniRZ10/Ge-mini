from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, update
from typing import List, Optional
from datetime import datetime, timezone
from ...domain.entities import Conversation, Message
from ...domain.repositories.interfaces import ConversationRepository, MessageRepository
from .models import ConversationModel, MessageModel

class SqlAlchemyConversationRepository(ConversationRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self, limit: int = 50) -> List[Conversation]:
        query = select(ConversationModel).order_by(ConversationModel.updated_at.desc()).limit(limit)
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [Conversation.model_validate(m) for m in models]

    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        query = select(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self.session.execute(query)
        model = result.scalar_one_or_none()
        return Conversation.model_validate(model) if model else None

    async def create(self, conversation: Conversation) -> Conversation:
        model = ConversationModel(
            id=conversation.id,
            title=conversation.title,
            created_at=conversation.created_at,
            updated_at=conversation.updated_at
        )
        self.session.add(model)
        return Conversation.model_validate(model)

    async def delete(self, conversation_id: str) -> bool:
        query = delete(ConversationModel).where(ConversationModel.id == conversation_id)
        result = await self.session.execute(query)
        return result.rowcount > 0

    async def touch(self, conversation_id: str):
        now = datetime.now(timezone.utc)
        query = update(ConversationModel).where(ConversationModel.id == conversation_id).values(updated_at=now)
        await self.session.execute(query)

class SqlAlchemyMessageRepository(MessageRepository):
    def __init__(self, session: AsyncSession):
        self.session = session

    async def add(self, message: Message) -> Message:
        model = MessageModel(
            conversation_id=message.conversation_id,
            role=message.role,
            content=message.content,
            model=message.model,
            provider=message.provider,
            created_at=message.created_at
        )
        self.session.add(model)
        return Message.model_validate(model)

    async def get_by_conversation(self, conversation_id: str) -> List[Message]:
        query = select(MessageModel).where(MessageModel.conversation_id == conversation_id).order_by(MessageModel.created_at.asc())
        result = await self.session.execute(query)
        models = result.scalars().all()
        return [Message.model_validate(m) for m in models]
