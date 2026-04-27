from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..infrastructure.database.session import get_db
from ..infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from ..infrastructure.ai.factory import AiProviderFactory
from ..application.services.chat_service import ChatService

# Configuración global
SYSTEM_PROMPT = """
Eres Ge-mini, un asistente técnico experto.
NORMAS DE ESTILO:
1. Ve directo a la respuesta. Evita introducciones como "¡Claro!" o "Aquí tienes".
2. Usa Markdown estándar (prohibido LaTeX). Matemáticas con: x, *, /, ^.
3. Si el código o cálculo es complejo, prioriza la robustez y legibilidad.
4. Mantén el contexto de los mensajes anteriores de forma natural.
5. Responde siempre con un tono profesional, preciso y sin rodeos.
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
