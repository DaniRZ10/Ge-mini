# Guía de Instalación — Ge-mini

## Instalación automática

El instalador configura todo por ti: Python, entorno virtual, Ollama, modelos de IA local y claves API. No necesitas instalar nada previamente.

| Plataforma | Comando |
|---|---|
| Windows | Doble clic en `install.bat` |
| Linux | `sh install.sh` en la raíz del proyecto |

---

## Paso a paso

### Paso 1 — Entorno Python

El instalador descarga e instala **uv** (gestor de paquetes ultrarrápido), Python 3.12 y crea el entorno virtual `.venv` automáticamente.

> Si ya tienes `.venv`, este paso se salta.

### Paso 2 — Ollama

Ollama es el motor que ejecuta los modelos de IA en tu máquina.

- **Linux:** se instala ejecutando el script oficial de ollama.com (puede pedir contraseña `sudo`).
- **Windows:** se descarga y ejecuta el instalador silencioso `OllamaSetup.exe`.

Si Ollama ya está instalado, se verifica que el servicio esté activo. Si no está corriendo, el instalador lo arranca automáticamente.

### Paso 3 — Modelos de IA local

El instalador muestra un menú con los 5 modelos disponibles:

| Nº | Modelo | Descripción | Tamaño |
|---|---|---|---|
| 1 | Qwen 2.5 Coder 1.5B | Código, ligero | ~1.5 GB |
| 2 | Qwen 2.5 Coder 3B | Código, equilibrado | ~2.5 GB |
| 3 | Phi 3.5 Mini | Razonamiento | ~3.0 GB |
| 4 | Mistral 7B Instruct | General, maduro | ~4.8 GB |
| 5 | Qwen 2.5 Coder 7B | Código, potente | ~5.2 GB |

**Selección:**
- `1,3` → descarga los modelos 1 y 3
- `t` → descarga todos
- `n` (o Enter) → ninguno, puedes hacerlo más tarde

Los modelos no descargados aparecerán **deshabilitados** en el selector de la interfaz con un mensaje explicativo.

> Si no tienes conexión o Ollama no responde, puedes omitir este paso y re-ejecutar `install.sh` / `install.bat` en otro momento.

### Paso 4 — Claves API

Se solicitan (opcionales):

- **GEMINI_API_KEY** → Google Gemini. Formato: `AIzaSy` + 33 caracteres.  
  Obtener en: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)

- **GROQ_API_KEY** → Groq (modelos Llama en la nube). Formato: `gsk_` + mínimo 52 caracteres.  
  Obtener en: [console.groq.com/keys](https://console.groq.com/keys)

Si ya existe un archivo `.env`, este paso se omite automáticamente.

> Puedes dejar cualquier clave en blanco con Enter. Solo perderás acceso a ese proveedor.

### Paso 5 — Base de datos y arranque

Se ejecutan las migraciones de Alembic para preparar la base de datos SQLite y se lanza el servidor en `http://127.0.0.1:8000`.

El navegador se abre automáticamente al finalizar.

---

## Arranques posteriores

Una vez instalado, usa los scripts de arranque rápido:

| Plataforma | Comando |
|---|---|
| Windows | Doble clic en `start.bat` |
| Linux | `sh start.sh` |

Estos scripts:
1. Verifican que `.venv` existe.
2. Arrancan Ollama si está instalado pero no activo.
3. Abren el navegador.
4. Lanzan el servidor.

---

## Resolución de problemas

### El instalador dice "Ollama no responde"

Ollama puede tardar en arrancar en equipos lentos. Espera unos segundos y vuelve a ejecutar el instalador, o arranca Ollama manualmente con `ollama serve` en una terminal aparte.

### Los modelos locales aparecen deshabilitados en la interfaz

Dos causas posibles:
1. **Ollama no está activo** — ejecuta `start.bat` / `sh start.sh` para que arranque automáticamente.
2. **El modelo no está descargado** — vuelve a ejecutar `install.bat` / `sh install.sh` y selecciona el modelo.

### Error al instalar Ollama en Windows

El instalador de Ollama puede requerir permisos de administrador. Si falla, instala Ollama manualmente desde [ollama.com](https://ollama.com/download) y vuelve a ejecutar el instalador.

### Quiero cambiar mis claves API

Edita el archivo `.env` en la raíz del proyecto con cualquier editor de texto. El archivo tiene este formato:

```env
OLLAMA_BASE_URL=http://localhost:11434
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...
```

---

## Instalación manual (macOS / avanzado)

Si prefieres instalar manualmente o estás en macOS:

```bash
# 1. Instalar uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# 2. Crear entorno virtual
uv python install 3.12
uv venv .venv --python 3.12
uv pip install -r requirements.txt

# 3. Instalar Ollama
curl -fsSL https://ollama.com/install.sh | sh

# 4. Descargar modelos (ejemplo)
ollama pull qwen2.5-coder:1.5b

# 5. Crear .env con tus claves
echo "GEMINI_API_KEY=tu_clave_aqui" > .env

# 6. Migraciones y arranque
.venv/bin/python -m alembic upgrade head
.venv/bin/python -m uvicorn app.main:app --port 8000
```
