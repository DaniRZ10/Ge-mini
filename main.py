"""
Ge-mini — Backend principal (FastAPI)
=====================================
Este módulo inicializa la aplicación web, configura el servidor
de archivos estáticos para la interfaz de usuario y define los 
endpoints de la API para procesar los mensajes del chat.
"""

from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles  # Utilizado para servir archivos estáticos como HTML, CSS y JS
from pydantic import BaseModel  # Utilizado para la validación y serialización de datos
import os
from dotenv import load_dotenv
from google import genai
from google.genai import errors

# Cargar variables de entorno desde el archivo .env
load_dotenv()

# Cliente de Gemini
API_KEY = os.getenv("GEMINI_API_KEY")
if not API_KEY:
    print("ADVERTENCIA: No se ha configurado 'GEMINI_API_KEY' en el entorno.")
    gemini_client = None
else:
    gemini_client = genai.Client(api_key=API_KEY)

# ──────────────────────────────────────────────
# 1. Inicialización de la aplicación
# ──────────────────────────────────────────────
# Se crea la instancia principal de FastAPI. Aquí se pueden configurar
# metadatos como el título, descripción y versión de la API que luego
# se mostrarán en la documentación automática (Swagger UI).
app: FastAPI = FastAPI(
    title="Ge-mini API",
    description="Clon de ChatGPT potenciado por Google Gemini",
    version="0.1.0",
)

# ──────────────────────────────────────────────
# 2. Servir archivos estáticos de Frontend
# ──────────────────────────────────────────────
# FastAPI permite "montar" una aplicación o un directorio estático en una ruta específica.
# Al montar el directorio "static" en la ruta "/static", todos los archivos contenidos 
# en esta carpeta (como index.html, estilos o scripts) estarán accesibles al cliente.
app.mount("/static", StaticFiles(directory="static"), name="static")

# ──────────────────────────────────────────────
# 3. Modelos de datos (Pydantic)
# ──────────────────────────────────────────────
# Pydantic se encarga de validar los datos de entrada y salida basándose 
# en anotaciones de tipos de Python de manera automática.

class ChatRequest(BaseModel):
    """
    Define la estructura requerida para los mensajes que envía el cliente web.
    Se espera recibir un objeto JSON con una propiedad 'message' de tipo texto.
    """
    message: str


class ChatResponse(BaseModel):
    """
    Define la estructura de la respuesta que el servidor devolverá al cliente.
    Garantiza que la API siempre responda con un JSON consistente.
    """
    response: str


# ──────────────────────────────────────────────
# 4. Definición de Endpoints (Rutas)
# ──────────────────────────────────────────────

@app.get("/")
async def root() -> dict[str, str]:
    """
    Ruta raíz de la API. Realiza un 'health-check' sencillo para
    verificar que el servidor está levantado y funcionando correctamente.
    """
    return {"status": "Ge-mini backend is alive 🚀"}


# En FastAPI, definimos el verbo HTTP (post) y la ruta ("/api/chat").
# response_model indica qué modelo de Pydantic usar para validar/serializar la respuesta.
@app.post("/api/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Endpoint principal para interactuar con el modelo de chat.
    
    FastAPI inyecta la carga útil (payload) de la petición HTTP automáticamente en 
    el parámetro 'request', validando el JSON recibido contra el esquema 'ChatRequest'.
    """
    if not gemini_client:
        raise HTTPException(
            status_code=500, 
            detail="El servidor no tiene configurada la clave de la API de Gemini."
        )

    try:
        # Hacemos la petición a Google Gemini
        response = gemini_client.models.generate_content(
            model='gemini-2.5-flash',
            contents=request.message,
        )
        
        reply_text = response.text if response.text else "Lo siento, no generé ninguna respuesta válida."
        return ChatResponse(response=reply_text)
        
    except errors.APIError as e:
        raise HTTPException(status_code=502, detail=f"Error en la API de Gemini: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno del servidor: {str(e)}")
