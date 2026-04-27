import os
import httpx
import time
from typing import List
from ...domain.entities import Message
from ...domain.providers.base import AiProvider

class OllamaAdapter(AiProvider):
    def __init__(self, system_prompt: str):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.system_prompt = system_prompt

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        url = f"{self.base_url}/api/chat"
        
        # Preparar mensajes para Ollama
        ollama_messages = [{"role": "system", "content": self.system_prompt}]
        
        for m in history:
            role = "user" if m.role == "user" else "assistant"
            ollama_messages.append({"role": role, "content": m.content})
            
        # Añadir mensaje actual
        ollama_messages.append({"role": "user", "content": message})
        
        payload = {
            "model": model_id,
            "messages": ollama_messages,
            "stream": False
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
                
                # Log para que el asistente pueda leerlo
                print(f"\n[BENCHMARK] Modelo: {model_id} | Latencia: {latency:.2f}s | Palabras: {len(content.split())}")
                
                return content
            except Exception as e:
                return f"Error conectando con Ollama: {str(e)}"
