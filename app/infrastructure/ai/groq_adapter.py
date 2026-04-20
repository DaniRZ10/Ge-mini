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
        
        # Añadir el mensaje actual del usuario
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages
        )
        
        reply_text = response.choices[0].message.content
        return reply_text if reply_text else "El modelo no devolvió una respuesta válida."
