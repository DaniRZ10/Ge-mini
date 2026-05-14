from google import genai
from google.genai import types, errors
from typing import List, AsyncIterator
import logging

from ...domain.entities import Message
from ...domain.providers.base import AiProvider

class GeminiAdapter(AiProvider):
    def __init__(self, api_key: str, system_prompt: str):
        self.api_key = api_key
        self.system_prompt = system_prompt
        self._client = genai.Client(api_key=api_key)
        self._config = (
            types.GenerateContentConfig(system_instruction=system_prompt)
            if system_prompt
            else None
        )

    @property
    def name(self) -> str:
        return "gemini"

    def _prepare_history(self, history: List[Message]) -> List[types.Content]:
        contents: List[types.Content] = []
        for m in history:
            role = "user" if m.role == "user" else "model"
            contents.append(
                types.Content(role=role, parts=[types.Part.from_text(text=m.content)])
            )
        return contents

    async def list_models(self) -> List[dict]:
        """Lista los modelos disponibles en la cuenta."""
        try:
            result: List[dict] = []
            async for m in await self._client.aio.models.list():
                actions = m.supported_actions or []
                if "generateContent" not in actions:
                    continue
                model_id = (m.name or "").split("/")[-1]
                result.append({"id": model_id, "name": m.display_name})
            return result
        except Exception as e:
            logging.error(f"Error listando modelos Gemini: {e}")
            return []

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        try:
            contents = self._prepare_history(history)
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=message)])
            )

            response = await self._client.aio.models.generate_content(
                model=model_id,
                contents=contents,
                config=self._config,
            )
            return response.text or ""
        except errors.APIError as e:
            if getattr(e, "code", None) == 429:
                return "Error: Has agotado tu cuota de Gemini (Rate Limit). Por favor, espera un minuto o prueba con otro modelo."
            return f"Error en Gemini SDK: {str(e)}"
        except Exception as e:
            return f"Error en Gemini SDK: {str(e)}"

    def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        return self._send_message_stream_gen(message, history, model_id)

    async def _send_message_stream_gen(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        try:
            contents = self._prepare_history(history)
            contents.append(
                types.Content(role="user", parts=[types.Part.from_text(text=message)])
            )

            stream = await self._client.aio.models.generate_content_stream(
                model=model_id,
                contents=contents,
                config=self._config,
            )
            async for chunk in stream:
                if chunk.text:
                    yield chunk.text
        except errors.APIError as e:
            if getattr(e, "code", None) == 429:
                yield "Error: Cuota agotada (Rate Limit). Reintenta en un minuto."
            else:
                yield f"Error en streaming Gemini: {str(e)}"
        except Exception as e:
            yield f"Error en streaming Gemini: {str(e)}"
