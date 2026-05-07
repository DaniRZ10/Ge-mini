# Ge-mini 💠

Ge-mini es una interfaz de chat inteligente, minimalista y de alto rendimiento que permite interactuar con múltiples modelos de IA (Google Gemini, Groq/Llama y **IA Local con Ollama**) desde una única plataforma unificada.

![Thumbnail](docs/screenshot.png)

## ✨ Características Principales

- **🤖 Multimodelo:** Selector dinámico para cambiar entre Gemini, Llama (Groq) e **IA Local (Ollama)** en tiempo real.
- **⚡ Real-Time Streaming:** Respuestas instantáneas palabra a palabra gracias a la implementación de `StreamingResponse` y `ReadableStream`.
- **🧠 Memoria Unificada:** Cambia de modelo a mitad de una conversación sin perder el contexto. Soporte total para el historial incluso en modelos locales.
- **🌓 Dual Theme:** Soporte completo para Modo Oscuro (Premium) y Modo Claro con persistencia en el navegador.
- **🎨 Estética Refinada:** Interfaz premium con transiciones suaves, **glassmorphism** y "Smart Scroll".
- **🛠 Gestión de Cuotas:** Detección automática de errores de límite de tokens con mensajes amigables.
- **🛡️ Seguridad:** Sanitización XSS integrada con `DOMPurify` para un renderizado seguro de Markdown.
- **📜 Migraciones:** Gestión de base de datos profesional con **Alembic**.

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
│   ├── application/    # Lógica de orquestación (Servicios de Chat)
│   ├── infrastructure/ # Implementaciones (SQLAlchemy, AI Adapters)
│   ├── core/           # Configuración global (Logging)
│   └── main.py         # Punto de entrada FastAPI
├── migrations/         # Versiones de base de datos (Alembic)
├── static/             # Frontend (HTML, CSS con Glassmorphism, JS)
├── data/               # Base de datos SQLite
├── tests/              # Suite de pruebas SDD (pytest)
└── .specify/           # Especificaciones del diseño (SDD)
```

## 🛠 Tecnologías Utilizadas

- **Backend:** FastAPI con Clean Architecture.
- **ORM/Persistencia:** SQLAlchemy 2.0 (Async) + Alembic para migraciones.
- **Frontend:** JavaScript Vanilla + DOMPurify (Seguridad) + Marked.js.
- **Logging:** Módulo `logging` configurado para depuración estructurada.
- **IA Cloud:** SDK Oficial de Google Generative AI + Groq SDK.

---
*Desarrollado con ❤️ para el proyecto Ge-mini.*
