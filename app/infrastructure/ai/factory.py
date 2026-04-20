import os
from .gemini_adapter import GeminiAdapter
from .groq_adapter import GroqAdapter
from ...domain.providers.base import AiProvider

class AiProviderFactory:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")

    def get_provider(self, model_id: str) -> AiProvider:
        if model_id.startswith("gemini"):
            if not self.gemini_key:
                raise ValueError("GEMINI_API_KEY no configurada.")
            return GeminiAdapter(self.gemini_key, self.system_prompt)
        
        if "llama" in model_id or "mixtral" in model_id:
            if not self.groq_key:
                raise ValueError("GROQ_API_KEY no configurada.")
            return GroqAdapter(self.groq_key, self.system_prompt)
        
        raise ValueError(f"Modelo '{model_id}' no soportado o proveedor no encontrado.")
