import pytest
import os
import asyncio
from httpx import AsyncClient, ASGITransport
from unittest.mock import MagicMock, patch

# Configuramos la variable de entorno ANTES de importar la app
# para que app.database use la ruta de test.
TEST_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "test_gemini.db")
os.environ["DATABASE_URL"] = TEST_DB_PATH

from app.main import app
from app import database as db

@pytest.fixture(scope="session", autouse=True)
def setup_test_env():
    """Configuración global antes de todos los tests."""
    # Asegurarnos de que no usamos claves reales accidentalmente (opcional)
    # os.environ["GEMINI_API_KEY"] = "mock_key"
    # os.environ["GROQ_API_KEY"] = "mock_key"
    yield
    # Limpieza final: borrar la BD de test si existe
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

@pytest.fixture(autouse=True)
async def initialize_db():
    """Inicializa la BD antes de cada test para tener un estado limpio."""
    await db.init_db()
    yield
    # Podríamos limpiar tablas aquí si fuera necesario

@pytest.fixture
async def client():
    """Proporciona un cliente httpx configurado para la app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

@pytest.fixture(autouse=True)
def mock_ai_clients():
    """
    Mockea automáticamente los clientes de Gemini y Groq en app.main.
    Se ejecuta para cada test automáticamente.
    """
    with patch("app.main.clients") as mock_clients:
        # Mock para Gemini
        mock_gemini = MagicMock()
        # Simulamos la respuesta de session.send_message(user_msg).text
        mock_gemini.chats.create.return_value.send_message.return_value.text = "Hola! Soy tu Ge-mini de prueba."
        
        # Mock para Groq
        mock_groq = MagicMock()
        # Simulamos response.choices[0].message.content
        mock_groq.chat.completions.create.return_value.choices[0].message.content = "Respuesta simulada de Llama vía Groq."
        
        # Asignamos al diccionario de clientes
        mock_clients.__getitem__.side_effect = lambda k: {
            "gemini": mock_gemini,
            "groq": mock_groq
        }.get(k)
        
        # Para que clients.get(provider) funcione
        mock_clients.get.side_effect = lambda k: {
            "gemini": mock_gemini,
            "groq": mock_groq
        }.get(k)
        
        yield mock_clients
