import google.generativeai as genai
from google.api_core import exceptions, retry
from typing import List, AsyncIterator
import asyncio

from ...domain.entities import Message
from ...domain.providers.base import AiProvider

class GeminiAdapter(AiProvider):
    def __init__(self, api_key: str, system_prompt: str):
        self.api_key = api_key
        self.system_prompt = system_prompt
        genai.configure(api_key=api_key)

    def _prepare_history(self, history: List[Message]):
        contents = []
        for m in history:
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [m.content]})
        return contents

    async def list_models(self) -> List[dict]:
        """Lista los modelos disponibles en la cuenta."""
        try:
            loop = asyncio.get_event_loop()
            models = await loop.run_in_executor(None, lambda: list(genai.list_models()))
            
            return [
                {"id": m.name.split("/")[-1], "name": m.display_name}
                for m in models if "generateContent" in m.supported_generation_methods
            ]
        except Exception as e:
            print(f"Error listando modelos Gemini: {e}")
            return []

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        try:
            model = genai.GenerativeModel(
                model_name=model_id,
                system_instruction=self.system_prompt if self.system_prompt else None
            )
            
            chat = model.start_chat(history=self._prepare_history(history))
            
            # El SDK ya maneja reintentos básicos, pero podemos ser explícitos
            response = await model.generate_content_async(
                message,
                request_options={"retry": retry.Retry(predicate=retry.if_exception_type(exceptions.ResourceExhausted))}
            )
            return response.text
        except exceptions.ResourceExhausted:
            return "Error: Has agotado tu cuota de Gemini (Rate Limit). Por favor, espera un minuto o prueba con otro modelo."
        except Exception as e:
            return f"Error en Gemini SDK: {str(e)}"

    async def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        try:
            model = genai.GenerativeModel(
                model_name=model_id,
                system_instruction=self.system_prompt if self.system_prompt else None
            )
            
            contents = self._prepare_history(history)
            contents.append({"role": "user", "parts": [message]})
            
            response = await model.generate_content_async(
                contents,
                stream=True,
                request_options={"retry": retry.Retry(predicate=retry.if_exception_type(exceptions.ResourceExhausted))}
            )
            
            async for chunk in response:
                if chunk.text:
                    yield chunk.text
        except exceptions.ResourceExhausted:
            yield "Error: Cuota agotada (Rate Limit). Reintenta en un minuto."
        except Exception as e:
            yield f"Error en streaming Gemini: {str(e)}"
