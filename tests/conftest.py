"""
Configuración de tests para Ge-mini.
- BD SQLite en MEMORIA (aislada, rápida)
- FakeProvider que simula respuestas de IA sin red
- Override de dependencias FastAPI
"""
import pytest
import asyncio
from typing import List, AsyncIterator, Any
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession

from app.domain.entities import Message
from app.domain.providers.base import AiProvider
from app.infrastructure.database.models import Base
from app.api.dependencies import get_conversation_repo, get_message_repo, get_chat_service
from app.infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from app.application.services.chat_service import ChatService
from app.infrastructure.ai.factory import AiProviderFactory


# ─── Fake AI Provider (sin red, sin APIs) ───

class FakeProvider(AiProvider):
    """Proveedor de IA falso para tests. Devuelve respuestas predecibles."""

    @property
    def name(self) -> str:
        return "fake"

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        return f"Respuesta fake para: {message}"

    def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        return self._send_message_stream_gen(message, history, model_id)

    async def _send_message_stream_gen(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        words = f"Streaming fake para: {message}".split()
        for word in words:
            yield word + " "


class FakeProviderFactory(AiProviderFactory):
    """Fábrica que siempre devuelve el FakeProvider."""
    
    def __init__(self, system_prompt: str = ""):
        super().__init__(system_prompt)
    
    def get_provider(self, model_id: str) -> AiProvider:
        return FakeProvider()


# ─── Infraestructura de Base de Datos para Tests ───

TEST_DB_URL = "sqlite+aiosqlite:///:memory:"
TEST_ENGINE = create_async_engine(TEST_DB_URL, echo=False)
TestSessionLocal = async_sessionmaker(TEST_ENGINE, expire_on_commit=False, class_=AsyncSession)

@pytest.fixture(scope="session")
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
async def setup_db():
    """Crea las tablas antes de cada test y las limpia después."""
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with TEST_ENGINE.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncIterator[AsyncSession]:
    """Fixture que provee una sesión de base de datos aislada por test."""
    async with TestSessionLocal() as session:
        yield session


# ─── Cliente HTTP para Integration Tests ───

@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncIterator[AsyncClient]:
    """
    Fixture que provee un cliente HTTP conectado a la app,
    con las dependencias de BD e IA sobreescritas para usar mocks/memoria.
    """
    from app.main import app
    from app.infrastructure.database.session import get_db
    
    # Overrides
    async def override_get_db():
        yield db_session
        
    def override_get_ai_factory():
        return FakeProviderFactory()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_chat_service] = lambda: ChatService(
        db_session, 
        SqlAlchemyConversationRepository(db_session), 
        SqlAlchemyMessageRepository(db_session), 
        FakeProviderFactory()
    )
    
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
        
    app.dependency_overrides.clear()


# ─── NUEVAS FIXTURES (Spec-Driven Development) ───

class ControllableProvider(AiProvider):
    """
    Provider altamente configurable para tests de comportamiento complejo.
    Permite inyectar hooks y registrar llamadas.
    
    ATRIBUTOS:
    - `provider_name`: nombre que devuelve el provider.
    - `response`: respuesta estática predefinida.
    - `side_effect`: si es una Exception, se lanza; si es valor, se devuelve.
    - `call_log`: lista de tuplas (method, model_id) para verificar orden.
    - `on_send_hook`: callable opcional que se invoca dentro de send_message
      (útil para simular un switch de modelo mientras la request está en vuelo).
    """

    def __init__(
        self,
        provider_name: str = "test",
        response: str = "respuesta controlada",
        side_effect: Any = None
    ):
        self._name = provider_name
        self._response = response
        self.side_effect = side_effect
        self.call_log: List[tuple] = []
        self.on_send_hook = None

    @property
    def name(self) -> str:
        return self._name

    async def send_message(self, message: str, history: List[Message], model_id: str) -> str:
        """Simula envío registrando la llamada y activando hooks."""
        self.call_log.append(("send_message", model_id))
        
        if self.side_effect and isinstance(self.side_effect, Exception):
            raise self.side_effect
            
        if self.on_send_hook:
            self.on_send_hook()
            
        return self._response

    def send_message_stream(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        return self._send_message_stream_gen(message, history, model_id)

    async def _send_message_stream_gen(self, message: str, history: List[Message], model_id: str) -> AsyncIterator[str]:
        """Simula streaming registrando la llamada."""
        self.call_log.append(("send_message_stream", model_id))
        
        if self.side_effect:
            if isinstance(self.side_effect, Exception):
                raise self.side_effect
            yield str(self.side_effect)
            return

        if self.on_send_hook:
            self.on_send_hook()
            
        words = self._response.split()
        for word in words:
            yield word + " "
            await asyncio.sleep(0.01)


class SwitchableFactory(AiProviderFactory):
    """
    Fábrica de providers con estado mutable.
    Simula el concepto de 'modelo activo' para los tests de Spec 1.
    """

    def __init__(self, initial_provider: AiProvider):
        super().__init__("")
        self._provider = initial_provider

    def switch_to(self, new_provider: AiProvider) -> None:
        """Cambia el provider activo (simula cambio de modelo por el usuario)."""
        self._provider = new_provider

    def get_provider(self, model_id: str) -> AiProvider:
        return self._provider


@pytest.fixture
def provider_a():
    return ControllableProvider(provider_name="provider_a", response="Respuesta del modelo A")

@pytest.fixture
def provider_b():
    return ControllableProvider(provider_name="provider_b", response="Respuesta del modelo B")

@pytest.fixture
def provider_c():
    return ControllableProvider(provider_name="provider_c", response="Respuesta del modelo C")

@pytest.fixture
def local_down_provider():
    """Simula un modelo local (Ollama) que falla por conexión/memoria."""
    import httpx
    return ControllableProvider(
        provider_name="ollama",
        side_effect=httpx.ConnectError("Ollama connection refused (simulated)")
    )

@pytest.fixture
def cloud_provider():
    return ControllableProvider(provider_name="gemini", response="Respuesta desde la nube")


@pytest.fixture
def override_chat_service():
    """
    Fixture de contexto para inyectar factories en get_chat_service.
    Simplifica el patrón try/finally repetido en los tests.

    Uso:
        factory = SwitchableFactory(initial_provider=provider_a)
        with override_chat_service(factory):
            response = await client.post("/api/chat", ...)
    """
    from app.main import app

    class OverrideContext:
        def __init__(self, factory: AiProviderFactory):
            self.factory = factory

        async def __aenter__(self):
            async def _override():
                async with TestSessionLocal() as session:
                    conv_repo = SqlAlchemyConversationRepository(session)
                    msg_repo = SqlAlchemyMessageRepository(session)
                    yield ChatService(session, conv_repo, msg_repo, self.factory)

            app.dependency_overrides[get_chat_service] = _override
            return self

        async def __aexit__(self, _exc_type, _exc_val, _exc_tb):
            app.dependency_overrides.pop(get_chat_service, None)

    def _make_context(factory: AiProviderFactory):
        return OverrideContext(factory)

    return _make_context
