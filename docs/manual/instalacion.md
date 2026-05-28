# Guía de Instalación — Ge-mini

## Instalación automática

El instalador configura todo por ti: Python, entorno virtual, Ollama, modelos de IA local y claves API. No necesitas instalar nada previamente.

| Plataforma | Comando |
|---|---|
| Windows | Doble clic en `install.bat` |
| Linux | `sh install.sh` en la raíz del proyecto |

---

## Qué hace el instalador

Al iniciarse, el instalador muestra un mensaje de bienvenida y detalla los 5 pasos que va a ejecutar. También detecta automáticamente la RAM de tu equipo y la usa para recomendarte modelos apropiados.

---

## Paso a paso

### Paso 1 — Entorno Python

El instalador descarga e instala **uv** (gestor de paquetes ultrarrápido), Python 3.12 y crea el entorno virtual `.venv` automáticamente.

> Si ya tienes `.venv`, este paso se salta.

### Paso 2 — Ollama

Ollama es el motor que ejecuta los modelos de IA en tu máquina.

- **Linux:** se instala ejecutando el script oficial de ollama.com.
- **Windows:** se descarga y ejecuta el instalador silencioso `OllamaSetup.exe`.

Si Ollama ya está instalado, se verifica que el servicio esté activo. Si no está corriendo, el instalador lo arranca automáticamente.

### Paso 3 — Modelos de IA local

El instalador detecta tu RAM y calcula los modelos que caben cómodamente en tu equipo (RAM total − 2 GB de margen para el SO).

Muestra una tabla con los 11 modelos del catálogo:

| Nº | Modelo | Uso | RAM | Estado |
|---|---|---|---|---|
| 1 | Qwen Coder 0.5B | Código, ultra ligero | 2 GB | [OK]/[*]/[!]/[ ] |
| 2 | Llama 3.2 1B | Chat ligero | 2 GB | |
| 3 | Qwen Coder 1.5B | Código, ligero | 3 GB | |
| 4 | Llama 3.2 3B | Chat general | 5 GB | |
| 5 | Qwen Coder 3B | Código, equilibrado | 5 GB | |
| 6 | Phi 3.5 Mini | Razonamiento | 6 GB | |
| 7 | Mistral 7B Instruct | General, maduro | 8 GB | |
| 8 | Qwen Coder 7B | Código, capaz | 8 GB | |
| 9 | Llama 3.1 8B | Multipropósito | 8 GB | |
| 10 | Qwen 2.5 14B | Razonamiento avanzado | 12 GB | |
| 11 | Mixtral 8x7B | Top tier MoE | 28 GB | |

**Marcadores de estado:**
- `[OK]` — ya descargado en este equipo
- `[*]` — recomendado según tu RAM
- `[!]` — excede tu RAM disponible
- `[ ]` — disponible, pero no recomendado prioritariamente

**Selección:**
- `r` o Enter → descarga los recomendados
- `1,3,5` → descarga los modelos 1, 3 y 5
- `t` → descarga todos
- `n` → ninguno (puedes hacerlo más tarde)

**Tags personalizados:** al terminar la selección del catálogo, puedes introducir tags adicionales de Ollama (por ejemplo, `codellama:13b`). El instalador los descargará. Pulsa Enter sin escribir nada para terminar.

Los modelos no descargados aparecerán **deshabilitados** en el selector de la interfaz con un mensaje explicativo.

> Si Ollama no responde, puedes omitir este paso y re-ejecutar el instalador en otro momento.

### Paso 4 — Modelos cloud (opcional)

El instalador pregunta si quieres configurar proveedores en la nube. **Este paso es completamente opcional** — si no introduces ninguna clave, la aplicación funciona perfectamente con los modelos locales.

Si respondes `s`:
- Puedes seleccionar uno, dos o los tres proveedores.
- El instalador valida el formato de cada clave y hace un ping HTTP real al proveedor para confirmar que funciona.
- Si ya tienes claves configuradas en `.env`, no se te pedirán de nuevo.

**Proveedores disponibles:**

| Nº | Proveedor | Modelos | Formato de clave |
|---|---|---|---|
| 1 | Google Gemini | Gemini 2.5 Flash, 1.5 Flash, 1.5 Pro | `AIzaSy` + 33 chars |
| 2 | Groq (Llama) | Llama 3.3 70B, Llama 3.1 8B | `gsk_` + 52+ chars |
| 3 | Anthropic (Claude) | Claude Opus 4.7, Sonnet 4.6, Haiku 4.5 | `sk-ant-` + 80+ chars |

> **Aviso de coste:** Claude Opus 4.7 tiene un coste elevado por token (~$15/M output). El instalador te avisará antes de pedirte la clave.

Dónde obtener las claves:
- Gemini: [aistudio.google.com/app/apikey](https://aistudio.google.com/app/apikey)
- Groq: [console.groq.com/keys](https://console.groq.com/keys)
- Anthropic: [console.anthropic.com](https://console.anthropic.com/)

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

## Añadir un proveedor cloud después de la instalación

Si en su momento omitiste configurar un proveedor cloud y ahora quieres añadirlo:

**Opción A — Reinstalar:**
Vuelve a ejecutar `install.bat` / `sh install.sh`. El instalador detectará tu `.env` existente y solo te pedirá las claves que faltan.

**Opción B — Editar `.env` a mano:**
Abre el archivo `.env` en la raíz del proyecto con cualquier editor de texto y añade la línea correspondiente:

```env
OLLAMA_BASE_URL=http://localhost:11434
GEMINI_API_KEY=AIzaSy...
GROQ_API_KEY=gsk_...
ANTHROPIC_API_KEY=sk-ant-...
```

Reinicia el servidor para que tome los cambios.

---

## Cómo la interfaz muestra la disponibilidad

Al cargar la página, `checkAllModelsAvailability()` consulta simultáneamente el estado local y cloud:

- **Modelos locales:** deshabilitados si Ollama no está activo o el modelo no está descargado.
- **Modelos cloud:** deshabilitados si la clave no está configurada o no es válida. Si el validador detecta que la clave guardada ha dejado de funcionar, el modelo se deshabilita con un tooltip explicativo.

Si el modelo que tenías seleccionado queda deshabilitado, la interfaz selecciona automáticamente el primero disponible.

---

## Resolución de problemas

### El instalador dice "Ollama no responde"

Ollama puede tardar en arrancar en equipos lentos. Espera unos segundos y vuelve a ejecutar el instalador, o arranca Ollama manualmente con `ollama serve` en una terminal aparte.

### Los modelos locales aparecen deshabilitados

Dos causas posibles:
1. **Ollama no está activo** — ejecuta `start.bat` / `sh start.sh` para que arranque automáticamente.
2. **El modelo no está descargado** — vuelve a ejecutar el instalador y selecciona el modelo.

### Error al instalar Ollama en Windows

El instalador de Ollama puede requerir permisos de administrador. Si falla, instala Ollama manualmente desde [ollama.com](https://ollama.com/download) y vuelve a ejecutar el instalador.

### Los modelos cloud aparecen deshabilitados

- **Sin clave API:** sigue las instrucciones de "Añadir un proveedor cloud después de la instalación".
- **Clave inválida:** la clave guardada en `.env` puede haberse revocado. Genera una nueva en la consola del proveedor y actualiza `.env`.

---

## macOS

macOS no está soportado en esta versión. Está previsto para una release futura.
