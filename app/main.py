"""
Ge-mini — Proyecto Antigravity 💠
=====================================
Servidor FastAPI refactorizado con Clean Architecture.
"""

import os
import uuid
from dotenv import load_dotenv
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import StreamingResponse
from fastapi.staticfiles import StaticFiles

# Infraestructura y Capas
from .infrastructure.database.session import init_db
from .core.logging import setup_logging
from .api.schemas import ChatRequest, ChatResponse, ConversationOut, MessageOut
from .api.dependencies import get_chat_service, get_conversation_repo, get_message_repo
from .infrastructure.ai.gemini_adapter import GeminiAdapter
from .infrastructure.ai.ollama_adapter import get_ollama_installed_models
from .infrastructure.ai.factory import KNOWN_LOCAL_MODELS
from .infrastructure.database.repositories import SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
from .application.services.chat_service import ChatService

# Cargar variables de entorno
load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa servicios al arrancar."""
    setup_logging()
    await init_db()
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
    import os
    if os.getenv("GEMINI_API_KEY"): providers.append("gemini")
    if os.getenv("GROQ_API_KEY"): providers.append("groq")
    return {"status": "Ge-mini is alive and Clean 💠", "providers": providers}

@app.get("/api/models/gemini")
async def list_gemini_models():
    """Descubre dinámicamente los modelos de Gemini disponibles."""
    import os
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        return []
    
    adapter = GeminiAdapter(api_key, "")
    return await adapter.list_models()

@app.get("/api/models/local/status")
async def local_model_status():
    """Estado en tiempo real de los modelos Ollama. HTTP 200 siempre; ollama_running indica si el servicio está activo."""
    all_tags = [m["tag"] for m in KNOWN_LOCAL_MODELS]
    all_checks = {m["tag"]: m["check"] for m in KNOWN_LOCAL_MODELS}
    installed, running = await get_ollama_installed_models()
    available = [
        tag for tag, check in all_checks.items()
        if any(check in name for name in installed)
    ]
    return {"available": available, "all": all_tags, "ollama_running": running}

# --- Endpoints: Conversaciones ---

@app.get("/api/conversations", response_model=list[ConversationOut])
async def list_conversations(
    repo: SqlAlchemyConversationRepository = Depends(get_conversation_repo)
):
    convs = await repo.get_all()
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
    conv_id = request.conversation_id or str(uuid.uuid4())
    
    try:
        # 1. Persistir mensaje del usuario inmediatamente
        await service.persist_user_message(request.message, request.model, conv_id)
        
        async def stream_and_save():
            """Wrapper: emite chunks al frontend y asegura la persistencia de lo recibido."""
            full_reply = ""
            try:
                async for chunk in service.get_stream_generator(
                    message_content=request.message,
                    model_id=request.model,
                    conversation_id=conv_id
                ):
                    full_reply += chunk
                    yield chunk
            finally:
                # 2. Persistir lo que hayamos recibido, sea completo o parcial
                if full_reply:
                    await service.persist_assistant_message(full_reply, request.model, conv_id)
        
        return StreamingResponse(
            stream_and_save(),
            media_type="text/event-stream",
            headers={"X-Conversation-Id": conv_id}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error en streaming: {str(e)}")
