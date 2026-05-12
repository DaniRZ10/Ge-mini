from typing import List, AsyncIterator
from groq import AsyncGroq
from ...domain.entities import Message
from ...domain.providers.base import AiProvider

class GroqAdapter(AiProvider):
    def __init__(self, api_key: str, system_prompt: str):
        self.client = AsyncGroq(api_key=api_key)
        self.system_prompt = system_prompt

    @property
    def name(self) -> str:
        return "groq"

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        messages = [{"role": "system", "content": self.system_prompt}]
        for m in history:
            messages.append({"role": m.role, "content": m.content})
        
        messages.append({"role": "user", "content": message})
        
        # Groq SDK espera tipos específicos, pero dict funciona en runtime. 
        # Cast Any para evitar errores de lint si es necesario.
        response = await self.client.chat.completions.create(
            model=model_id,
            messages=messages, # type: ignore
            temperature=0.7
        )
        
        reply_text = response.choices[0].message.content
        return reply_text if reply_text else "El modelo no devolvió una respuesta válida."

    def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        return self._send_message_stream_gen(message, history, model_id)

    async def _send_message_stream_gen(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        messages = [{"role": "system", "content": self.system_prompt}]
        for m in history:
            messages.append({"role": m.role, "content": m.content})
        messages.append({"role": "user", "content": message})
        
        response = await self.client.chat.completions.create(
            model=model_id,
            messages=messages, # type: ignore
            stream=True 
        )
        async for chunk in response:
            content = chunk.choices[0].delta.content
            if content:
                yield content
