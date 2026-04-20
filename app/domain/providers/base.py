from abc import ABC, abstractmethod
from typing import List
from ..entities import Message

class AiProvider(ABC):
    @abstractmethod
    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        """Envía un mensaje al proveedor de IA y devuelve la respuesta."""
        pass
