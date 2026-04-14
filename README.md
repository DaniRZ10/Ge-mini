# Ge-mini

Ge-mini es un clon ligero inspirado en ChatGPT, desarrollado con un backend moderno en Python y una interfaz frontend responsiva e intuitiva con diseño en modo oscuro (Dark Mode). Su objetivo es proporcionar una experiencia de chat rápida, enlazando directamente con los modelos de lenguaje de Google Gemini.

## 🚀 Tecnologías Utilizadas

- **Backend:** FastAPI (Python), Uvicorn.
- **Inteligencia Artificial:** Google Gemini SDK.
- **Frontend:** HTML5, CSS3 (Grid/Flexbox) y Vanilla JavaScript.
- **Control de Versiones:** Git y GitHub.

## ⚙️ Funcionamiento Actual

Hasta el momento, el proyecto cuenta con la estructura fundamental:
- **FastAPI:** Configurado con un endpoint de prueba en `main.py`.
- **Frontend:** Estructura básica de la interfaz en `static/index.html`.
- **Servidor:** Configuración de archivos estáticos y entorno virtual (`.venv`) listos y excluidos del control de versiones.

## 📌 Funcionalidades Deseadas (Roadmap)

A medida que el proyecto avance, se irán implementando y actualizando las siguientes funcionalidades:

- [x] Integración completa con el SDK de Google Gemini para procesar prompts reales.
- [ ] Construcción del área de chat en el UI (lista de mensajes de usuario y respuestas del asistente).
- [x] Manejo del estado del chat (mantener historial de la conversación en sesión).
- [ ] Efectos visuales de "escribiendo" y animaciones fluidas (Smooth Scrolling, Hover effects).
- [ ] Interfaz completamente responsiva (optimizada para dispositivos móviles).
- [ ] Botón para alternar entre Modo Oscuro y Modo Claro (si aplica a futuro).
- [ ] Soporte para visualización de código en Markdown dentro de las respuestas de Gemini.

## 🛠️ Cómo ejecutar localmente

1. Clona el repositorio.
2. Crea y activa tu entorno virtual:
   ```bash
   python -m venv .venv
   .venv\Scripts\activate
   ```
3. Instala las dependencias:
   ```bash
   pip install -r requirements.txt
   ```
4. Levanta el servidor con Uvicorn:
   ```bash
   uvicorn main:app --reload
   ```

---
*Este documento se irá actualizando activamente conforme se desarrollen nuevas características.*
