# Ge-mini 💠

Ge-mini es una interfaz de chat inteligente, minimalista y de alto rendimiento que permite interactuar con múltiples modelos de IA (Google Gemini, Groq/Llama y **IA Local con Ollama**) desde una única plataforma unificada.

![Thumbnail](docs/screenshot.png)

## ✨ Características Principales

- **🤖 Multimodelo:** Selector dinámico para cambiar entre Gemini, Llama (Groq) e **IA Local (Ollama)** en tiempo real.
- **⚡ Real-Time Streaming:** Respuestas instantáneas palabra a palabra gracias a la implementación de `StreamingResponse` y `ReadableStream`.
- **🧠 Memoria Unificada:** Cambia de modelo a mitad de una conversación sin perder el contexto. Soporte total para el historial incluso en modelos locales.
- **🌓 Dual Theme:** Soporte completo para Modo Oscuro (Premium) y Modo Claro con persistencia en el navegador.
- **🎨 Estética Refinada:** Interfaz inspirada en las mejores prácticas de UI/UX modernas, con transiciones suaves y "Smart Scroll" para lectura fluida.
- **🛠 Gestión de Cuotas:** Detección automática de errores de límite de tokens con mensajes amigables para el usuario.

## 🚀 Instalación Rápida

1. **Clonar el repositorio:**
   ```bash
   git clone https://github.com/DaniRZ10/Ge-mini.git
   cd Ge-mini
   ```

2. **Crear entorno virtual e instalar dependencias:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # En Windows: .venv\Scripts\activate
   pip install -r requirements.txt
   ```

3. **Configurar variables de entorno (`.env`):**
   Crea un archivo `.env` en la raíz con tus claves de API:
   ```env
   GEMINI_API_KEY=tu_clave_aqui
   GROQ_API_KEY=tu_clave_aqui
   OLLAMA_BASE_URL=http://localhost:11434
   ```

4. **Lanzar el servidor:**
   ```bash
   uvicorn app.main:app --reload
   ```
   *También puedes usar el script automatizado en Windows: `tools\start_app.bat`*

5. **Acceder:**
   Abre [http://127.0.0.1:8000/static/index.html](http://127.0.0.1:8000/static/index.html) en tu navegador.

## 🧪 Pruebas (Testing)

Para ejecutar los tests automatizados y asegurar que todo funciona:
- **Windows:** Ejecuta `tools\run_tests.bat`.
- **Manual (Terminal):** `.venv\Scripts\python.exe -m pytest`.


## 📂 Estructura del Proyecto (Clean Architecture)

```text
Ge-mini/
├── app/
│   ├── domain/         # Entidades puras e interfaces (Repository/Provider)
│   ├── application/    # Casos de uso y lógica de orquestación (Servicios)
│   ├── infrastructure/ # Implementaciones concretas (SQLAlchemy, AI Adapters)
│   ├── api/            # Routers de FastAPI, Schemas (DTOs) y Dependencias
│   └── main.py         # Punto de entrada de la aplicación
├── docs/               # Capturas y documentación técnica (Gamma export)
├── static/             # Frontend (HTML, CSS, JS)
├── data/               # Base de datos SQLite (gemini_chat.db)
├── tools/              # Scripts de ejecución (.bat)
├── requirements.txt    # Dependencias del proyecto
└── .env                # Configuración secreta
```

## 🛠 Tecnologías Utilizadas

- **Backend:** FastAPI (Python 3.10+) con Clean Architecture.
- **ORM/Persistencia:** SQLAlchemy 2.0 (Async) + aiosqlite.
- **Frontend:** HTML5, CSS3 Variables, JavaScript Vanilla.
- **IA Local:** Ollama SDK (Patrón Strategy/Adapter).
- **IA Cloud:** Google GenAI SDK, Groq SDK.
- **Markdown:** Marked.js para el renderizado de respuestas.

---
*Desarrollado con ❤️ para el proyecto Ge-mini.*
