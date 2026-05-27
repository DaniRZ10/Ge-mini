"""Adapter para Anthropic Claude (Opus, Sonnet, Haiku)."""

from typing import List, AsyncIterator
from anthropic import AsyncAnthropic, APIError
from ...domain.entities import Message
from ...domain.providers.base import AiProvider


class AnthropicAdapter(AiProvider):
    def __init__(self, api_key: str, system_prompt: str):
        self.api_key = api_key
        self.system_prompt = system_prompt
        self.client = AsyncAnthropic(api_key=api_key)

    @property
    def name(self) -> str:
        return "anthropic"

    def _prepare_messages(self, history: List[Message], message: str) -> List[dict]:
        """Anthropic exige alternar user/assistant y NO acepta 'system' en messages."""
        messages = []
        for m in history:
            role = "user" if m.role == "user" else "assistant"
            messages.append({"role": role, "content": m.content})
        messages.append({"role": "user", "content": message})
        return messages

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        try:
            messages = self._prepare_messages(history, message)
            kwargs = {
                "model": model_id,
                "max_tokens": 4096,
                "messages": messages,
            }
            if self.system_prompt:
                kwargs["system"] = self.system_prompt

            response = await self.client.messages.create(**kwargs)
            if response.content and len(response.content) > 0:
                return response.content[0].text
            return "El modelo no devolvió una respuesta válida."
        except APIError as e:
            if getattr(e, "status_code", None) == 429:
                return "Error: Cuota agotada en Anthropic (Rate Limit). Espera o prueba otro modelo."
            if getattr(e, "status_code", None) == 401:
                return "Error: Clave Anthropic inválida o expirada. Verifica tu ANTHROPIC_API_KEY."
            return f"Error en Anthropic SDK: {str(e)}"
        except Exception as e:
            return f"Error en Anthropic SDK: {str(e)}"

    def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        return self._send_message_stream_gen(message, history, model_id)

    async def _send_message_stream_gen(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        try:
            messages = self._prepare_messages(history, message)
            kwargs = {
                "model": model_id,
                "max_tokens": 4096,
                "messages": messages,
            }
            if self.system_prompt:
                kwargs["system"] = self.system_prompt

            async with self.client.messages.stream(**kwargs) as stream:
                async for text in stream.text_stream:
                    if text:
                        yield text
        except APIError as e:
            if getattr(e, "status_code", None) == 429:
                yield "Error: Cuota agotada (Rate Limit). Reintenta en un minuto."
            elif getattr(e, "status_code", None) == 401:
                yield "Error: Clave Anthropic inválida."
            else:
                yield f"Error en streaming Anthropic: {str(e)}"
        except Exception as e:
            yield f"Error en streaming Anthropic: {str(e)}"
