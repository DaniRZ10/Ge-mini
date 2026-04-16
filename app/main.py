"""
Ge-mini — Proyecto Antigravity 💠
=====================================
Servidor FastAPI para una interfaz de chat multimodelo.
Soporta Google Gemini y Groq (familia Llama).
Persiste el historial de conversaciones en SQLite.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# SDKs de los proveedores
from google import genai
from google.genai import errors as gemini_errors
from groq import Groq, GroqError

# Módulo de base de datos local
from app import database as db

# Cargar configuración
load_dotenv()

# Inicialización de Clientes
clients = {
    "gemini": None,
    "groq": None
}

if os.getenv("GEMINI_API_KEY"):
    clients["gemini"] = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

if os.getenv("GROQ_API_KEY"):
    clients["groq"] = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Instrucción de sistema — Define la personalidad y reglas del asistente
SYSTEM_PROMPT = """
Eres Ge-mini, un asistente de IA creado por Dani. Sigue estas reglas:
1. Responde siempre de forma clara, concisa y directa.
2. No muestres tu proceso de razonamiento ni correcciones internas.
3. Si no estás seguro de un dato, dilo honestamente en vez de inventar.
4. Usa formato Markdown cuando mejore la legibilidad (listas, negritas, código).
5. Responde en el mismo idioma en el que te hablen.
""".strip()


# ─── Ciclo de vida de la app (inicializar BD al arrancar) ─────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos al arrancar el servidor."""
    await db.init_db()
    print("[OK] Base de datos SQLite inicializada.")
    yield


app: FastAPI = FastAPI(
    title="Ge-mini Multi-Model API",
    version="0.3.0",
    lifespan=lifespan,
)

# Montar archivos estáticos (HTML/CSS/JS)
# directory="static" funciona si ejecutamos uvicorn desde la raíz del proyecto
app.mount("/static", StaticFiles(directory="static"), name="static")


# ─── Modelos de request/response ──────────────────────────────────

class ChatRequest(BaseModel):
    message: str
    model: str                          # El modelo de IA seleccionado
    conversation_id: str | None = None  # None = crear conversación nueva

class ChatResponse(BaseModel):
    response: str
    provider: str
    conversation_id: str                # Siempre devolvemos el ID

class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str

class MessageOut(BaseModel):
    id: int
    role: str
    content: str
    model: str | None
    provider: str | None
    created_at: str


# ─── Endpoints: Conversaciones ────────────────────────────────────

@app.get("/")
async def root():
    return {"status": "Ge-mini is alive 🚀", "providers": [k for k, v in clients.items() if v]}


@app.get("/api/conversations", response_model=list[ConversationOut])
async def list_conversations():
    """Devuelve todas las conversaciones, ordenadas por más reciente."""
    convs = await db.list_conversations()
    return convs


@app.get("/api/conversations/{conversation_id}/messages", response_model=list[MessageOut])
async def get_messages(conversation_id: str):
    """Devuelve los mensajes de una conversación específica."""
    messages = await db.get_conversation_messages(conversation_id)
    if not messages:
        # Verificamos si la conversación existe (podría tener 0 mensajes)
        convs = await db.list_conversations()
        if not any(c["id"] == conversation_id for c in convs):
            raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    return messages


@app.delete("/api/conversations/{conversation_id}")
async def delete_conversation(conversation_id: str):
    """Borra una conversación y todos sus mensajes."""
    deleted = await db.delete_conversation(conversation_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Conversación no encontrada.")
    return {"status": "Conversación eliminada"}


# ─── Endpoint principal: Chat ─────────────────────────────────────

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Recibe el mensaje del usuario, selecciona el modelo correspondiente
    y devuelve la respuesta de la IA. Persiste todo en la BD.
    """
    model_id = request.model
    user_msg = request.message
    conversation_id = request.conversation_id

    # Determinar qué proveedor usar basándose en el ID del modelo
    provider = ""
    if model_id.startswith("gemini"):
        provider = "gemini"
    elif "llama" in model_id or "mixtral" in model_id:
        provider = "groq"

    if not clients.get(provider):
        raise HTTPException(
            status_code=400, 
            detail=f"No tienes configurada la API Key para el proveedor '{provider}'."
        )

    # Si no hay conversation_id, creamos una nueva conversación
    if not conversation_id:
        title = user_msg[:50] + ("..." if len(user_msg) > 50 else "")
        conversation_id = await db.create_conversation(title)

    # Guardar el mensaje del usuario en la BD
    await db.add_message(conversation_id, "user", user_msg, model_id, provider)

    # Cargar historial completo de la conversación para dar contexto al modelo
    history = await db.get_conversation_messages(conversation_id)

    try:
        reply_text = ""
        
        # --- Lógica por Proveedor ---
        
        if provider == "gemini":
            # Adaptar historial a formato Gemini (sin el último mensaje que enviamos ahora)
            gemini_history = []
            for m in history[:-1]:
                role = "user" if m["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [{"text": m["content"]}]})
            
            # Crear sesión temporal con historial, system prompt y enviar
            session = clients["gemini"].chats.create(
                model=model_id,
                history=gemini_history,
                config={"system_instruction": SYSTEM_PROMPT}
            )
            response = session.send_message(user_msg)
            reply_text = response.text

        elif provider == "groq":
            # Formato estándar de Groq (con system prompt al inicio)
            groq_messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            for m in history:
                groq_messages.append({"role": m["role"], "content": m["content"]})
            
            response = clients["groq"].chat.completions.create(
                model=model_id,
                messages=groq_messages
            )
            reply_text = response.choices[0].message.content

        if not reply_text:
            reply_text = "El modelo no devolvió una respuesta válida."

        # Guardar respuesta del asistente en la BD
        await db.add_message(conversation_id, "assistant", reply_text, model_id, provider)
        
        return ChatResponse(
            response=reply_text,
            provider=provider,
            conversation_id=conversation_id
        )

    except Exception as e:
        error_str = str(e).lower()
        detail = f"Error: {str(e)}"
        
        # Mapeo de errores de cuota (Rate limits)
        if any(kw in error_str for kw in ["429", "quota", "limit", "exhausted"]):
            detail = "⚠️ Cuota agotada en este modelo. Prueba a cambiar de proveedor en el panel lateral."
        
        raise HTTPException(status_code=502, detail=detail)
