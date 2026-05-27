import os
from .gemini_adapter import GeminiAdapter
from .groq_adapter import GroqAdapter
from .ollama_adapter import OllamaAdapter
from ...domain.providers.base import AiProvider

# Modelos locales disponibles via Ollama.
# 'tag'   → argumento exacto para `ollama pull`.
# 'check' → substring para detectar si está instalado en `ollama list`.
# 'size'  → peso estimado en disco (informativo, usado por el instalador).
KNOWN_LOCAL_MODELS: list[dict] = [
    {"name": "Qwen 2.5 Coder 1.5B", "tag": "qwen2.5-coder:1.5b",         "check": "qwen2.5-coder:1.5b",   "size": "~1.5 GB"},
    {"name": "Qwen 2.5 Coder 3B",   "tag": "qwen2.5-coder:3b",            "check": "qwen2.5-coder:3b",     "size": "~2.5 GB"},
    {"name": "Phi 3.5 Mini",         "tag": "phi3.5:latest",               "check": "phi3.5",               "size": "~3.0 GB"},
    {"name": "Mistral 7B Instruct",  "tag": "mistral:7b-instruct-q4_K_M", "check": "mistral:7b-instruct",  "size": "~4.8 GB"},
    {"name": "Qwen 2.5 Coder 7B",   "tag": "qwen2.5-coder:7b",            "check": "qwen2.5-coder:7b",     "size": "~5.2 GB"},
]

# Set de tags para detección rápida en get_provider.
_LOCAL_MODEL_TAGS: set[str] = {m["tag"] for m in KNOWN_LOCAL_MODELS}


class AiProviderFactory:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")

    def get_provider(self, model_id: str) -> AiProvider:
        # Modelos locales: match exacto contra los tags conocidos.
        if model_id in _LOCAL_MODEL_TAGS:
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
