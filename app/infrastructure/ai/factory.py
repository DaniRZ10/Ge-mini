import os
from .gemini_adapter import GeminiAdapter
from .groq_adapter import GroqAdapter
from .ollama_adapter import OllamaAdapter
from .anthropic_adapter import AnthropicAdapter
from ...domain.providers.base import AiProvider


# Catálogo de modelos locales disponibles via Ollama.
# 'tag'      → argumento exacto para `ollama pull`.
# 'check'    → substring para detectar si está instalado en `ollama list`.
# 'ram_gb'   → RAM mínima estimada (Approx — refinar con benchmark data).
# 'category' → uso típico (mostrado en el wizard del instalador).
LOCAL_MODELS_CATALOG: list[dict] = [
    {"name": "Qwen Coder 0.5B",       "tag": "qwen2.5-coder:0.5b",          "check": "qwen2.5-coder:0.5b",   "ram_gb": 2,  "category": "Código, ultra ligero"},
    {"name": "Llama 3.2 1B",          "tag": "llama3.2:1b",                  "check": "llama3.2:1b",          "ram_gb": 2,  "category": "Chat ligero"},
    {"name": "Qwen Coder 1.5B",       "tag": "qwen2.5-coder:1.5b",          "check": "qwen2.5-coder:1.5b",   "ram_gb": 3,  "category": "Código, ligero"},
    {"name": "Llama 3.2 3B",          "tag": "llama3.2:3b",                  "check": "llama3.2:3b",          "ram_gb": 5,  "category": "Chat general"},
    {"name": "Qwen Coder 3B",         "tag": "qwen2.5-coder:3b",            "check": "qwen2.5-coder:3b",     "ram_gb": 5,  "category": "Código, equilibrado"},
    {"name": "Phi 3.5 Mini",          "tag": "phi3.5:latest",                "check": "phi3.5",               "ram_gb": 6,  "category": "Razonamiento"},
    {"name": "Mistral 7B Instruct",   "tag": "mistral:7b-instruct-q4_K_M",  "check": "mistral:7b-instruct",  "ram_gb": 8,  "category": "General, maduro"},
    {"name": "Qwen Coder 7B",         "tag": "qwen2.5-coder:7b",            "check": "qwen2.5-coder:7b",     "ram_gb": 8,  "category": "Código, capaz"},
    {"name": "Llama 3.1 8B",          "tag": "llama3.1:8b",                  "check": "llama3.1:8b",          "ram_gb": 8,  "category": "Multipropósito"},
    {"name": "Qwen 2.5 14B",          "tag": "qwen2.5:14b",                  "check": "qwen2.5:14b",          "ram_gb": 12, "category": "Razonamiento avanzado"},
    {"name": "Mixtral 8x7B",          "tag": "mixtral:8x7b",                 "check": "mixtral:8x7b",         "ram_gb": 28, "category": "Top tier MoE"},
]

# Set de tags para detección rápida en get_provider.
_LOCAL_MODEL_TAGS: set[str] = {m["tag"] for m in LOCAL_MODELS_CATALOG}

# Alias retrocompatible para el endpoint /api/models/local/status.
KNOWN_LOCAL_MODELS = LOCAL_MODELS_CATALOG


class AiProviderFactory:
    def __init__(self, system_prompt: str):
        self.system_prompt = system_prompt
        self.gemini_key = os.getenv("GEMINI_API_KEY")
        self.groq_key = os.getenv("GROQ_API_KEY")
        self.anthropic_key = os.getenv("ANTHROPIC_API_KEY")

    def get_provider(self, model_id: str) -> AiProvider:
        if model_id in _LOCAL_MODEL_TAGS:
            return OllamaAdapter(self.system_prompt)

        if model_id.lower().startswith("gemini"):
            if not self.gemini_key:
                raise ValueError("GEMINI_API_KEY no configurada.")
            return GeminiAdapter(self.gemini_key, self.system_prompt)

        if model_id.lower().startswith("claude"):
            if not self.anthropic_key:
                raise ValueError("ANTHROPIC_API_KEY no configurada.")
            return AnthropicAdapter(self.anthropic_key, self.system_prompt)

        if "llama" in model_id or "mixtral" in model_id:
            if not self.groq_key:
                raise ValueError("GROQ_API_KEY no configurada.")
            return GroqAdapter(self.groq_key, self.system_prompt)

        raise ValueError(f"Modelo '{model_id}' no soportado o proveedor no encontrado.")
