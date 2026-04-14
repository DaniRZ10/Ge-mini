"""
Ge-mini — Backend Multimodelo (FastAPI)
=====================================
Soporta Google Gemini, OpenAI GPT y Groq (Llama/Mixtral).
Gestiona una memoria de conversación unificada.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import os
from dotenv import load_dotenv

# SDKs de los proveedores
from google import genai
from google.genai import errors as gemini_errors
from openai import OpenAI, OpenAIError
from groq import Groq, GroqError

# Cargar configuración
load_dotenv()

# Inicialización de Clientes
clients = {
    "gemini": None,
    "openai": None,
    "groq": None
}

if os.getenv("GEMINI_API_KEY"):
    clients["gemini"] = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

if os.getenv("GROQ_API_KEY"):
    clients["groq"] = Groq(api_key=os.getenv("GROQ_API_KEY"))

# Memoria de conversación global (Unificada)
# Estructura: [{"role": "user"|"assistant", "content": "..."}]
chat_history = []

app: FastAPI = FastAPI(
    title="Ge-mini Multi-Model API",
    version="0.2.0",
)

app.mount("/static", StaticFiles(directory="static"), name="static")

class ChatRequest(BaseModel):
    message: str
    model: str  # Nuevo: el frontend envía el modelo seleccionado

class ChatResponse(BaseModel):
    response: str
    provider: str

@app.get("/")
async def root():
    return {"status": "Omni-Chat is alive 🚀", "providers": [k for k, v in clients.items() if v]}

@app.post("/api/clear")
async def clear_chat():
    global chat_history
    chat_history = []
    return {"status": "Memoria universal reiniciada"}

@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    global chat_history
    
    model_id = request.model
    user_msg = request.message
    
    # Determinar qué proveedor usar basándose en el ID del modelo
    provider = ""
    if model_id.startswith("gemini"):
        provider = "gemini"
    elif model_id.startswith("gpt"):
        provider = "openai"
    elif "llama" in model_id or "mixtral" in model_id:
        provider = "groq"
    
    if not clients.get(provider):
        raise HTTPException(
            status_code=400, 
            detail=f"No tienes configurada la API Key para el proveedor '{provider}'."
        )

    # Añadir mensaje del usuario al historial
    chat_history.append({"role": "user", "content": user_msg})

    try:
        reply_text = ""
        
        # --- Lógica por Proveedor ---
        
        if provider == "gemini":
            # Adaptar historial a formato Gemini
            gemini_history = []
            for m in chat_history[:-1]: # Todo menos el último que enviamos ahora
                role = "user" if m["role"] == "user" else "model"
                gemini_history.append({"role": role, "parts": [{"text": m["content"]}]})
            
            # Crear sesión temporal con historial y enviar
            session = clients["gemini"].chats.create(model=model_id, history=gemini_history)
            response = session.send_message(user_msg)
            reply_text = response.text

        elif provider == "groq":
            # Formato estándar de Groq (similar a OpenAI)
            response = clients["groq"].chat.completions.create(
                model=model_id,
                messages=chat_history
            )
            reply_text = response.choices[0].message.content

        if not reply_text:
            reply_text = "El modelo no devolvió una respuesta válida."

        # Guardar respuesta en el historial universal
        chat_history.append({"role": "assistant", "content": reply_text})
        
        return ChatResponse(response=reply_text, provider=provider)

    except Exception as e:
        # Limpiamos el último mensaje de usuario del historial si ha fallado para no corromper la memoria
        chat_history.pop()
        
        error_str = str(e).lower()
        detail = f"Error: {str(e)}"
        
        # Mapeo humano de errores de cuota (429)
        if "429" in error_str or "quota" in error_str or "limit" in error_str:
            detail = "⚠️ Has agotado los tokens o la cuota en este modelo. Prueba a seleccionar otro proveedor en el panel lateral."
        
        raise HTTPException(status_code=502, detail=detail)
