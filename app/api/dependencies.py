from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..infrastructure.database.session import get_db
from ..infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from ..infrastructure.ai.factory import AiProviderFactory
from ..application.services.chat_service import ChatService

# Configuración global (podría moverse a app/core/config.py)
SYSTEM_PROMPT = """
Eres Ge-mini, un asistente de IA creado por Dani. Sigue estas reglas:
1. Responde siempre de forma clara, precisa y con un lenguaje rico y natural.
2. No muestres tu proceso de razonamiento ni correcciones internas.
3. Si no estás seguro de un dato, dilo honestamente en vez de inventar.
4. Usa formato Markdown cuando mejore la legibilidad (listas, negritas, código).
5. Responde en el mismo idioma en el que te hablen.
""".strip()

def get_conversation_repo(session: AsyncSession = Depends(get_db)):
    return SqlAlchemyConversationRepository(session)

def get_message_repo(session: AsyncSession = Depends(get_db)):
    return SqlAlchemyMessageRepository(session)

def get_ai_factory():
    return AiProviderFactory(system_prompt=SYSTEM_PROMPT)

def get_chat_service(
    session: AsyncSession = Depends(get_db),
    conv_repo: SqlAlchemyConversationRepository = Depends(get_conversation_repo),
    msg_repo: SqlAlchemyMessageRepository = Depends(get_message_repo),
    ai_factory: AiProviderFactory = Depends(get_ai_factory)
):
    return ChatService(session, conv_repo, msg_repo, ai_factory)
