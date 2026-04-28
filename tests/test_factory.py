"""Tests unitarios de AiProviderFactory — routing de modelos."""
import pytest
import os
from unittest.mock import patch
from app.infrastructure.ai.factory import AiProviderFactory
from app.infrastructure.ai.gemini_adapter import GeminiAdapter
from app.infrastructure.ai.groq_adapter import GroqAdapter
from app.infrastructure.ai.ollama_adapter import OllamaAdapter


class TestFactoryRouting:
    """Verifica que la fábrica enruta cada modelo al adapter correcto."""

    @patch.dict(os.environ, {"GEMINI_API_KEY": "fake-key"})
    def test_routes_gemini_models(self):
        factory = AiProviderFactory(system_prompt="test")
        for model in ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-flash-latest"]:
            provider = factory.get_provider(model)
            assert isinstance(provider, GeminiAdapter), f"Fallo con modelo {model}"

    @patch.dict(os.environ, {"GROQ_API_KEY": "fake-key"})
    def test_routes_groq_models(self):
        factory = AiProviderFactory(system_prompt="test")
        for model in ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]:
            provider = factory.get_provider(model)
            assert isinstance(provider, GroqAdapter), f"Fallo con modelo {model}"

    def test_routes_ollama_models(self):
        factory = AiProviderFactory(system_prompt="test")
        for model in ["qwen2.5-coder:1.5b", "qwen2.5-coder:3b", "deepseek-coder:1.3b"]:
            provider = factory.get_provider(model)
            assert isinstance(provider, OllamaAdapter), f"Fallo con modelo {model}"

    def test_unknown_model_raises_error(self):
        factory = AiProviderFactory(system_prompt="test")
        with pytest.raises(ValueError, match="no soportado"):
            factory.get_provider("modelo-inventado-xyz")

    @patch.dict(os.environ, {}, clear=True)
    def test_gemini_without_key_raises(self):
        factory = AiProviderFactory(system_prompt="test")
        with pytest.raises(ValueError, match="GEMINI_API_KEY"):
            factory.get_provider("gemini-2.0-flash")

    @patch.dict(os.environ, {}, clear=True)
    def test_groq_without_key_raises(self):
        factory = AiProviderFactory(system_prompt="test")
        with pytest.raises(ValueError, match="GROQ_API_KEY"):
            factory.get_provider("llama-3.3-70b-versatile")

    def test_llama_instant_routes_to_groq_not_ollama(self):
        """'llama-3.1-8b-instant' contiene 'llama' y 'instant', debe ir a Groq."""
        factory = AiProviderFactory(system_prompt="test")
        factory.groq_key = "fake-key"
        provider = factory.get_provider("llama-3.1-8b-instant")
        assert isinstance(provider, GroqAdapter)
