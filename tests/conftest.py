"""
Configuración de tests para Ge-mini.
- BD SQLite en MEMORIA (aislada, rápida)
- FakeProvider que simula respuestas de IA sin red
- Override de dependencias FastAPI
"""
import pytest
import asyncio
from typing import List, AsyncIterator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.domain.entities import Message
from app.domain.providers.base import AiProvider
from app.infrastructure.database.models import Base
from app.api.dependencies import get_conversation_repo, get_message_repo, get_chat_service
from app.infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from app.application.services.chat_service import ChatService


# ─── Fake AI Provider (sin red, sin APIs) ───

class FakeProvider(AiProvider):
    """Proveedor de IA falso para tests. Devuelve respuestas predecibles."""

    @property
    def name(self) -> str:
        return "fake"

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        return f"Respuesta fake para: {message}"

    async def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        words = f"Streaming fake para: {message}".split()
        for word in words:
            yield word + " "


class FakeProviderFactory:
    """Fábrica que siempre devuelve el FakeProvider."""
    
    def __init__(self, system_prompt: str = ""):
        self.system_prompt = system_prompt
    
    def get_provider(self, model_id: str) -> AiProvider:
        return FakeProvider()


# ─── Motor de BD en memoria ───

TEST_ENGINE = create_async_engine("sqlite+aiosqlite://", echo=False)
TestSessionLocal = async_sessionmaker(TEST_ENGINE, expire_on_commit=False, class_=AsyncSession)


# ─── Fixtures ───

@pytest.fixture(scope="session")
def event_loop():
    """Crea un event loop compartido para toda la sesión de tests."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database():
    """Crea todas las tablas antes de cada test y las destruye después."""
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session():
    """Sesión de BD directa para tests unitarios."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client():
    """Cliente HTTP para tests de integración con dependencias sobreescritas."""
    from app.main import app

    # Override de TODAS las dependencias que usan BD o IA
    app.dependency_overrides[get_chat_service] = _get_test_chat_service
    app.dependency_overrides[get_conversation_repo] = _get_test_conversation_repo
    app.dependency_overrides[get_message_repo] = _get_test_message_repo
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    # Limpiar overrides
    app.dependency_overrides.clear()


# ─── Dependency Override Generators ───

async def _get_test_chat_service():
    """ChatService con BD de test y FakeProvider."""
    async with TestSessionLocal() as session:
        conv_repo = SqlAlchemyConversationRepository(session)
        msg_repo = SqlAlchemyMessageRepository(session)
        factory = FakeProviderFactory()
        yield ChatService(session, conv_repo, msg_repo, factory)


async def _get_test_conversation_repo():
    """Repositorio de conversaciones apuntando a la BD de test."""
    async with TestSessionLocal() as session:
        yield SqlAlchemyConversationRepository(session)


async def _get_test_message_repo():
    """Repositorio de mensajes apuntando a la BD de test."""
    async with TestSessionLocal() as session:
        yield SqlAlchemyMessageRepository(session)


# ─── Helpers para Spec 1 (Model Switch) y Spec 2 (Chat Persistence) ───
# TASK-02: fixtures compartidas para los nuevos test files.
# No duplican nada de lo anterior.

class ControllableProvider(AiProvider):
    """
    Provider configurable para tests.
    - `response`: texto que devuelve send_message.
    - `side_effect`: si se establece, send_message lanza esa excepción.
    - `call_log`: lista de tuplas (method, model_id) para verificar orden.
    - `on_send_hook`: callable opcional que se invoca dentro de send_message
      (útil para simular un switch de modelo mientras la request está en vuelo).
    """

    def __init__(
        self,
        provider_name: str = "test",
        response: str = "respuesta controlada",
        side_effect: Exception | None = None,
    ):
        self._name = provider_name
        self._response = response
        self._side_effect = side_effect
        self.call_log: list[tuple[str, str]] = []  # (method, model_id)
        self.on_send_hook = None  # callable() invocado en send_message

    @property
    def name(self) -> str:
        return self._name

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        self.call_log.append(("send_message", model_id))
        if self.on_send_hook:
            self.on_send_hook()
        if self._side_effect:
            raise self._side_effect
        return self._response

    async def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        self.call_log.append(("send_message_stream", model_id))
        yield self._response


class SwitchableFactory:
    """
    Fábrica de providers con estado mutable.
    Simula el concepto de 'modelo activo' para los tests de Spec 1:
    get_provider() siempre devuelve el provider actualmente registrado,
    y switch_to() permite cambiar ese provider en cualquier momento.
    """

    def __init__(self, initial_provider: AiProvider):
        self._provider = initial_provider

    def switch_to(self, new_provider: AiProvider) -> None:
        """Cambia el provider activo (simula cambio de modelo por el usuario)."""
        self._provider = new_provider

    def get_provider(self, model_id: str) -> AiProvider:
        return self._provider


@pytest.fixture
def provider_a() -> ControllableProvider:
    """Provider A — responde con éxito, registra sus llamadas."""
    return ControllableProvider(provider_name="provider_a", response="Respuesta del modelo A")


@pytest.fixture
def provider_b() -> ControllableProvider:
    """Provider B — responde con éxito, registra sus llamadas."""
    return ControllableProvider(provider_name="provider_b", response="Respuesta del modelo B")


@pytest.fixture
def provider_c() -> ControllableProvider:
    """Provider C — responde con éxito, registra sus llamadas."""
    return ControllableProvider(provider_name="provider_c", response="Respuesta del modelo C")


@pytest.fixture
def local_down_provider() -> ControllableProvider:
    """Provider local caído — lanza ConnectionError al intentar send_message."""
    import httpx
    return ControllableProvider(
        provider_name="ollama",
        side_effect=httpx.ConnectError("Connection refused: Ollama no está disponible"),
    )


@pytest.fixture
def cloud_provider() -> ControllableProvider:
    """Provider cloud de respaldo, siempre disponible."""
    return ControllableProvider(provider_name="gemini", response="Respuesta desde la nube")
