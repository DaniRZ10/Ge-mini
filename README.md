# Ge-mini 💠

Ge-mini es una interfaz de chat inteligente, minimalista y de alto rendimiento que permite interactuar con múltiples modelos de IA (Google Gemini, Anthropic Claude, Groq/Llama y **IA Local con Ollama**) desde una única plataforma unificada.

![Thumbnail](docs/screenshot.png)

## ✨ Características Principales

- **🤖 Multimodelo:** Selector dinámico para cambiar entre Gemini, Claude, Llama (Groq) e **IA Local (Ollama)** en tiempo real.
- **⚡ Real-Time Streaming:** Respuestas instantáneas palabra a palabra gracias a la implementación de `StreamingResponse` y `ReadableStream`.
- **🧠 Memoria Unificada:** Cambia de modelo a mitad de una conversación sin perder el contexto. Soporte total para el historial incluso en modelos locales.
- **🌓 Dual Theme:** Soporte completo para Modo Oscuro (Premium) y Modo Claro con persistencia en el navegador.
- **🎨 Estética Refinada:** Interfaz premium con transiciones suaves, **glassmorphism** y "Smart Scroll".
- **🛠 Gestión de Cuotas:** Detección automática de errores de límite de tokens con mensajes amigables.
- **🛡️ Seguridad:** Sanitización XSS integrada con `DOMPurify` para un renderizado seguro de Markdown.
- **📜 Migraciones:** Gestión de base de datos profesional con **Alembic**.
- **🔑 Modelos Cloud Inteligentes:** La UI detecta automáticamente qué proveedores están configurados y deshabilita los que no tienen clave válida.

## 🚀 Instalación

| Plataforma | Comando |
|---|---|
| Windows | Doble clic en **`install.bat`** |
| Linux | `sh install.sh` en la raíz del proyecto |

El instalador detecta tu RAM, recomienda los mejores modelos locales para tu equipo, y te pregunta si quieres configurar proveedores cloud (opcional). No se requiere ningún software previo.

Para arranques posteriores: **`start.bat`** (Windows) o **`sh start.sh`** (Linux).

> **macOS / instalación manual:** consulta [`docs/manual/instalacion.md`](docs/manual/instalacion.md).

## 🤖 Modelos Disponibles

### ☁️ Cloud

| Modelo | Proveedor | Clave necesaria |
|---|---|---|
| Gemini 2.5 Flash | Google | GEMINI_API_KEY — [obtener](https://aistudio.google.com/app/apikey) |
| Gemini 1.5 Flash | Google | GEMINI_API_KEY |
| Gemini 1.5 Pro | Google | GEMINI_API_KEY |
| Claude Opus 4.7 | Anthropic | ANTHROPIC_API_KEY — [obtener](https://console.anthropic.com/) |
| Claude Sonnet 4.6 | Anthropic | ANTHROPIC_API_KEY |
| Claude Haiku 4.5 | Anthropic | ANTHROPIC_API_KEY |
| Llama 3.3 (70B) | Groq | GROQ_API_KEY — [obtener](https://console.groq.com/keys) |
| Llama 3.1 (8B) | Groq | GROQ_API_KEY |

### 🖥️ Local (Ollama)

| Modelo | Tag | RAM mín. | Uso |
|---|---|---|---|
| Qwen Coder 0.5B | `qwen2.5-coder:0.5b` | 2 GB | Código, ultra ligero |
| Llama 3.2 1B | `llama3.2:1b` | 2 GB | Chat ligero |
| Qwen Coder 1.5B | `qwen2.5-coder:1.5b` | 3 GB | Código, ligero |
| Llama 3.2 3B | `llama3.2:3b` | 5 GB | Chat general |
| Qwen Coder 3B | `qwen2.5-coder:3b` | 5 GB | Código, equilibrado |
| Phi 3.5 Mini | `phi3.5:latest` | 6 GB | Razonamiento |
| Mistral 7B Instruct | `mistral:7b-instruct-q4_K_M` | 8 GB | General, maduro |
| Qwen Coder 7B | `qwen2.5-coder:7b` | 8 GB | Código, capaz |
| Llama 3.1 8B | `llama3.1:8b` | 8 GB | Multipropósito |
| Qwen 2.5 14B | `qwen2.5:14b` | 12 GB | Razonamiento avanzado |
| Mixtral 8x7B | `mixtral:8x7b` | 28 GB | Top tier MoE |

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
└── openspec/           # Especificaciones del diseño (SDD con OpenSpec)
```

## 🛠 Tecnologías Utilizadas

- **Backend:** FastAPI con Clean Architecture.
- **ORM/Persistencia:** SQLAlchemy 2.0 (Async) + Alembic para migraciones.
- **Frontend:** JavaScript Vanilla + DOMPurify (Seguridad) + Marked.js.
- **Logging:** Módulo `logging` configurado para depuración estructurada.
- **IA Cloud:** SDK `google-genai` (Google Gen AI SDK) + Groq SDK + Anthropic SDK.
- **IA Local:** Ollama — cualquier modelo GGUF disponible localmente.

---
*Desarrollado con ❤️ para el proyecto Ge-mini.*
