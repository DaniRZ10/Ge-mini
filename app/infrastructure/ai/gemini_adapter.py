import json
import httpx
from typing import List, AsyncIterator
from ...domain.entities import Message
from ...domain.providers.base import AiProvider

class GeminiAdapter(AiProvider):
    def __init__(self, api_key: str, system_prompt: str):
        self.api_key = api_key
        self.system_prompt = system_prompt

    def _get_url(self, model_id: str, stream: bool = False) -> str:
        # Usamos v1beta para máxima compatibilidad con todos los modelos de AI Studio
        version = "v1beta"
        base_url = f"https://generativelanguage.googleapis.com/{version}/models/{model_id}"
        
        if stream:
            return f"{base_url}:streamGenerateContent?alt=sse&key={self.api_key}"
        else:
            return f"{base_url}:generateContent?key={self.api_key}"

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        url = self._get_url(model_id)
        
        contents = []
        for m in history:
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})
        
        prompt_prefix = f"Instrucciones: {self.system_prompt}\n\nPregunta: " if self.system_prompt else ""
        contents.append({"role": "user", "parts": [{"text": f"{prompt_prefix}{message}"}]})
        
        async with httpx.AsyncClient() as client:
            resp = await client.post(url, json={"contents": contents}, timeout=30.0)
            if resp.status_code != 200:
                return f"Error de API Gemini ({resp.status_code}): {resp.text}"
            
            data = resp.json()
            return data['candidates'][0]['content']['parts'][0]['text']

    async def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        url = self._get_url(model_id, stream=True)
        
        contents = []
        for m in history:
            role = "user" if m.role == "user" else "model"
            contents.append({"role": role, "parts": [{"text": m.content}]})
        
        prompt_prefix = f"Instrucciones: {self.system_prompt}\n\nPregunta: " if self.system_prompt else ""
        contents.append({"role": "user", "parts": [{"text": f"{prompt_prefix}{message}"}]})

        async with httpx.AsyncClient(timeout=30.0) as client:
            async with client.stream("POST", url, json={"contents": contents}) as response:
                if response.status_code != 200:
                    yield f"Error de API Gemini ({response.status_code}): {await response.aread()}"
                    return

                async for line in response.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            json_str = line[6:].strip()
                            chunk_data = json.loads(json_str)
                            if "candidates" in chunk_data:
                                text = chunk_data['candidates'][0]['content']['parts'][0]['text']
                                yield text
                        except Exception:
                            continue
