from typing import List, AsyncIterator
from groq import Groq
from ...domain.entities import Message
from ...domain.providers.base import AiProvider

class GroqAdapter(AiProvider):
    def __init__(self, api_key: str, system_prompt: str):
        self.client = Groq(api_key=api_key)
        self.system_prompt = system_prompt

    @property
    def name(self) -> str:
        return "groq"

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        for m in history:
            messages.append({"role": m.role, "content": m.content})
        
        messages.append({"role": "user", "content": message})
        
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            temperature=0.7
        )
        
        reply_text = response.choices[0].message.content
        return reply_text if reply_text else "El modelo no devolvió una respuesta válida."

    async def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        # Stub de streaming para Groq
        messages = [{"role": "system", "content": self.system_prompt}]
        for m in history:
            messages.append({"role": m.role, "content": m.content})
        messages.append({"role": "user", "content": message})
        
        # En una implementación real, usaríamos stream=True y un bucle async
        response = self.client.chat.completions.create(
            model=model_id,
            messages=messages,
            stream=False 
        )
        yield response.choices[0].message.content
