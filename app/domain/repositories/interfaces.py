from abc import ABC, abstractmethod
from typing import List, Optional
from ..entities import Conversation, Message

class ConversationRepository(ABC):
    @abstractmethod
    async def get_by_id(self, conversation_id: str) -> Optional[Conversation]:
        pass

    @abstractmethod
    async def get_all(self) -> List[Conversation]:
        pass

    @abstractmethod
    async def create(self, conversation: Conversation) -> Conversation:
        pass

    @abstractmethod
    async def delete(self, conversation_id: str) -> bool:
        pass

    @abstractmethod
    async def touch(self, conversation_id: str):
        """Actualiza la fecha de modificación de la conversación."""
        pass

class MessageRepository(ABC):
    @abstractmethod
    async def get_by_conversation(self, conversation_id: str) -> List[Message]:
        pass

    @abstractmethod
    async def add(self, message: Message) -> Message:
        pass
