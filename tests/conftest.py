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
