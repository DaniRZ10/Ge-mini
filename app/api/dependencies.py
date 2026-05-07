import os
import secrets
from fastapi import Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from ..infrastructure.database.session import get_db
from ..infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from ..infrastructure.ai.factory import AiProviderFactory
from ..application.services.chat_service import ChatService

# Configuración global
SYSTEM_PROMPT = ""
APP_TOKEN = os.getenv("APP_TOKEN")

def require_token(authorization: str = Header(None)):
    """Verifica que el header Authorization: Bearer <token> sea válido."""
    if not APP_TOKEN:
        return # Permitir si no está configurado (uso local simple)
        
    expected = f"Bearer {APP_TOKEN}"
    if not authorization or not secrets.compare_digest(authorization, expected):
        raise HTTPException(status_code=401, detail="Unauthorized")

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
