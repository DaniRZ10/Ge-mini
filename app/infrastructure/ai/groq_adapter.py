from typing import List
from groq import Groq
from ...domain.entities import Message
from ...domain.providers.base import AiProvider

class GroqAdapter(AiProvider):
    def __init__(self, api_key: str, system_prompt: str):
        self.client = Groq(api_key=api_key)
        self.system_prompt = system_prompt

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        # Formato estándar de Groq
        messages = [{"role": "system", "content": self.system_prompt}]
        for m in history:
            messages.append({"role": m.role, "content": m.content})
        
        # El mensaje actual ya debería estar en el historial si seguimos la lógica del servicio,
        # pero por si acaso nos aseguramos de que el último mensaje sea el del usuario.
        # En el refactor actual, el servicio guardará el mensaje antes de llamar al provider.
        
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages
        )
        return response.choices[0].message.content
