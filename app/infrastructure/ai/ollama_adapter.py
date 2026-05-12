import os
import httpx
import time
import json
import logging
from typing import List, AsyncIterator
from ...domain.entities import Message
from ...domain.providers.base import AiProvider

class OllamaAdapter(AiProvider):
    def __init__(self, system_prompt: str):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.system_prompt = system_prompt

    @property
    def name(self) -> str:
        return "ollama"

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        url = f"{self.base_url}/api/chat"
        
        ollama_messages = []
        for i, m in enumerate(history):
            role = "user" if m.role == "user" else "assistant"
            content = m.content
            # Solo incrustar si el prompt no está vacío
            if i == 0 and role == "user" and self.system_prompt:
                content = f"Instrucciones del sistema:\n{self.system_prompt}\n\nMensaje del usuario:\n{content}"
            ollama_messages.append({"role": role, "content": content})
            
        final_message = message
        # Si no hay historial y hay prompt, inyectamos
        if not history and self.system_prompt:
            final_message = f"Instrucciones del sistema:\n{self.system_prompt}\n\nMensaje del usuario:\n{message}"
            
        ollama_messages.append({"role": "user", "content": final_message})
        
        payload = {
            "model": model_id,
            "messages": ollama_messages,
            "stream": False,
            "options": {"temperature": 0.2, "num_ctx": 4096}
        }
        
        start_time = time.time()
        async with httpx.AsyncClient(timeout=120.0) as client:
            try:
                response = await client.post(url, json=payload)
                response.raise_for_status()
                end_time = time.time()
                
                latency = end_time - start_time
                data = response.json()
                content = data["message"]["content"]
                
                logging.info(f"[BENCHMARK] Modelo: {model_id} | Latencia: {latency:.2f}s | Palabras: {len(content.split())}")
                
                return content
            except Exception as e:
                return f"Error conectando con Ollama: {str(e)}"

    def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        return self._send_message_stream_gen(message, history, model_id)

    async def _send_message_stream_gen(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        url = f"{self.base_url}/api/chat"
        
        ollama_messages = []
        for i, m in enumerate(history):
            role = "user" if m.role == "user" else "assistant"
            content = m.content
            # Solo incrustar si el prompt no está vacío
            if i == 0 and role == "user" and self.system_prompt:
                content = f"Instrucciones del sistema:\n{self.system_prompt}\n\nMensaje del usuario:\n{content}"
            ollama_messages.append({"role": role, "content": content})
            
        final_message = message
        if not history and self.system_prompt:
            final_message = f"Instrucciones del sistema:\n{self.system_prompt}\n\nMensaje del usuario:\n{message}"
            
        ollama_messages.append({"role": "user", "content": final_message})
        
        payload = {
            "model": model_id,
            "messages": ollama_messages,
            "stream": True,
            "options": {"temperature": 0.2, "num_ctx": 4096}
        }
        
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                async with client.stream("POST", url, json=payload) as response:
                    response.raise_for_status()
                    async for line in response.aiter_lines():
                        if not line:
                            continue
                        try:
                            chunk = json.loads(line)
                            if "message" in chunk and "content" in chunk["message"]:
                                yield chunk["message"]["content"]
                            if chunk.get("done"):
                                break
                        except json.JSONDecodeError:
                            continue
        except httpx.ConnectError:
            yield "\n\n[ERROR DEL SISTEMA]: Ollama ha dejado de responder. Esto ocurre frecuentemente si el modelo es demasiado grande para los 8GB de RAM del equipo (ej. Gemma 3) y provoca que el proceso colapse por falta de memoria."
        except Exception as e:
            yield f"\n\n[ERROR DEL SISTEMA]: {str(e)}"
