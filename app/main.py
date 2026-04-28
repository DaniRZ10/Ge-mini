"""
Ge-mini — Proyecto Antigravity 💠
=====================================
Servidor FastAPI refactorizado con Clean Architecture.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles
import os
from dotenv import load_dotenv

# Infraestructura y Capas
from .infrastructure.database.session import init_db
from .api.schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut
from .api.dependencies import get_chat_service, get_conversation_repo, get_message_repo
from .infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from .application.services.chat_service import ChatService

# Cargar variables de entorno
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos (SQLAlchemy) al arrancar."""
    await init_db()
    print("[OK] Base de datos (SQLAlchemy) inicializada.")
    yield

app = FastAPI(
    title="Ge-mini Multi-Model API",
    version="1.0.0",
    lifespan=lifespan,
)

# Archivos estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    providers = []
    if os.getenv("GEMINI_API_KEY"): providers.append("gemini")
    if os.getenv("GROQ_API_KEY"): providers.append("groq")
    return {"status": "Ge-mini is alive and Clean 💠", "providers": providers}

# --- Endpoints: Conversaciones ---

@app.get("/api/conversations", response_model=list[ConversationOut])
async def list_conversations(
    repo: SqlAlchemyConversationRepository = Depends(get_conversation_repo)
):
    convs = await repo.list_all()
    return [
        ConversationOut(
            id=c.id, 
            title=c.title, 
            created_at=c.created_at.isoformat(), 
            updated_at=c.updated_at.isoformat()
        ) for c in convs
    ]

@app.get("/api/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(
    conversation_id: str,
    repo: SqlAlchemyMessageRepository = Depends(get_message_repo)
):
    messages = await repo.get_by_conversation(conversation_id)
    if not messages:
        return []
    return [
        MessageOut(
            id=m.id,
            role=m.role,
            content=m.content,
            model=m.model,
            provider=m.provider,
            created_at=m.created_at.isoformat()
        ) for m in messages
    ]

@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    repo: SqlAlchemyConversationRepository = Depends(get_conversation_repo)
):
    async with repo.session.begin():
        deleted = await repo.delete(conversation_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    return {"status": "Conversación eliminada"}

# --- Endpoints principales: Chat ---

@app.post("/api/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    try:
        reply = await service.start_chat(
            message_content=request.message,
            model_id=request.model,
            conversation_id=request.conversation_id
        )
        return ChatResponse(
            response=reply.content,
            provider=reply.provider,
            conversation_id=reply.conversation_id
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")

@app.post("/api/chat/stream")
async def chat_stream(
    request: ChatRequest,
    service: ChatService = Depends(get_chat_service)
):
    """Endpoint de streaming para respuestas en tiempo real."""
    import uuid
    conv_id = request.conversation_id or str(uuid.uuid4())
    
    async def stream_and_save():
        """Wrapper: emite chunks al frontend y guarda en DB al terminar."""
        full_reply = ""
        async for chunk in service.get_stream_generator(
            message_content=request.message,
            model_id=request.model,
            conversation_id=conv_id
        ):
            full_reply += chunk
            yield chunk
        
        # Esto se ejecuta DESPUÉS de que el último chunk se haya enviado
        await service.save_stream_result(
            message_content=request.message,
            full_reply=full_reply,
            model_id=request.model,
            conversation_id=conv_id
        )
    
    try:
        return StreamingResponse(
            stream_and_save(),
            media_type="text/event-stream",
            headers={"X-Conversation-Id": conv_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en streaming: {str(e)}")
