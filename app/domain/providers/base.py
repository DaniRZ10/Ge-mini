from abc import ABC, abstractmethod
from typing import List, AsyncIterator
from ..entities import Message

class AiProvider(ABC):
    @abstractmethod
    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        """Envía un mensaje al proveedor de IA y devuelve la respuesta completa."""
        pass

    @abstractmethod
    async def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        """Envía un mensaje y devuelve un generador asíncrono de fragmentos de texto."""
        pass
