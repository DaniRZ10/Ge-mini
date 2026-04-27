from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..infrastructure.database.session import get_db
from ..infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from ..infrastructure.ai.factory import AiProviderFactory
from ..application.services.chat_service import ChatService

# Configuración global (podría moverse a app/core/config.py)
SYSTEM_PROMPT = """
Eres Ge-mini, un asistente de IA experto y directo creado por Dani.
REGLAS:
1. Responde de forma concisa, técnica y profesional.
2. Usa Markdown para mejorar la estructura (código, listas, negritas).
3. No menciones tus limitaciones ni des explicaciones innecesarias sobre tu naturaleza.
4. Si no conoces un dato, admítelo brevemente.
5. Prioriza la precisión técnica sobre la elocuencia.
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
