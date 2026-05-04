import os
from .gemini_adapter import GeminiAdapter
from .groq_adapter import GroqAdapter
from .ollama_adapter import OllamaAdapter
from ...domain.providers.base import AiProvider

class AiProviderFactory:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")

    def get_provider(self, model_id: str) -> AiProvider:
        # Detectar modelos de Ollama (si contienen 'qwen', 'deepseek', 'gemma', 'phi' o son explícitamente locales)
        local_models = ["qwen", "deepseek", "phi", "gemma", "starcoder", "llama3.1:8b", "codellama"]
        if any(m in model_id.lower() for m in local_models) and "instant" not in model_id:
            return OllamaAdapter(self.system_prompt)

        if model_id.lower().startswith("gemini"):
            if not self.gemini_key:
                raise ValueError("GEMINI_API_KEY no configurada.")
            return GeminiAdapter(self.gemini_key, self.system_prompt)
        
        if "llama" in model_id or "mixtral" in model_id:
            if not self.groq_key:
                raise ValueError("GROQ_API_KEY no configurada.")
            return GroqAdapter(self.groq_key, self.system_prompt)
        
        raise ValueError(f"Modelo '{model_id}' no soportado o proveedor no encontrado.")
