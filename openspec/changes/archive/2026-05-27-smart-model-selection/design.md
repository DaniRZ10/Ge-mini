# Design — smart-model-selection

## Goals

| ID | Goal |
|---|---|
| G1 | El instalador recomienda modelos apropiados al hardware del usuario. |
| G2 | Los proveedores cloud solo se configuran si el usuario los quiere. |
| G3 | Anthropic (Claude) disponible como tercer proveedor cloud. |
| G4 | La UI deshabilita modelos sin clave o sin Ollama, con tooltip descriptivo. |
| G5 | La validación de claves va más allá del formato: hace un ping HTTP real. |
| G6 | En reinstalación, el `.env` existente se respeta — no se pide lo ya configurado. |

## Non-Goals

- No se añade soporte multi-usuario.
- No se implementa selección de modelo por conversación en la UI.
- No se cambia la arquitectura de streaming.
- No se tocan migraciones ni la base de datos.

---

## D1 — Catálogo de modelos locales (11 entradas)

```
Tag                         | Nombre               | RAM GB | Categoría
qwen2.5-coder:0.5b          | Qwen Coder 0.5B      | 2      | Código, ultra ligero
llama3.2:1b                 | Llama 3.2 1B         | 2      | Chat ligero
qwen2.5-coder:1.5b          | Qwen Coder 1.5B      | 3      | Código, ligero
llama3.2:3b                 | Llama 3.2 3B         | 5      | Chat general
qwen2.5-coder:3b            | Qwen Coder 3B        | 5      | Código, equilibrado
phi3.5:latest               | Phi 3.5 Mini         | 6      | Razonamiento
mistral:7b-instruct-q4_K_M  | Mistral 7B Instruct  | 8      | General, maduro
qwen2.5-coder:7b            | Qwen Coder 7B        | 8      | Código, capaz
llama3.1:8b                 | Llama 3.1 8B         | 8      | Multipropósito
qwen2.5:14b                 | Qwen 2.5 14B         | 12     | Razonamiento avanzado
mixtral:8x7b                | Mixtral 8x7B         | 28     | Top tier MoE
```

**RAM usable** = RAM total − 2 GB (margen del SO).

---

## D2 — Algoritmo de recomendación

1. Filtrar modelos con `ram_gb <= RAM_usable` → lista `eligible`.
2. Si `eligible` vacío → recomendar índice 0 (el más ligero del catálogo).
3. Si `eligible` tiene 1-3 → recomendar todos.
4. Si `eligible` tiene ≥ 4 → seleccionar 3 representativos:
   - `eligible[0]` (más ligero accesible)
   - `eligible[len//2]` (punto medio)
   - `eligible[-1]` (el más capaz accesible)

---

## D3 — Wizard cloud opt-in

El instalador pregunta primero si el usuario quiere configurar proveedores cloud (s/N).

Si responde "s":
- Muestra los tres proveedores con indicador de si ya están configurados.
- Para cada proveedor seleccionado: si ya tiene clave, lo omite (idempotente).
- Para cada clave nueva: valida formato con regex + ping HTTP al proveedor.
- Aviso de coste antes de la clave de Anthropic Opus.

Lectura del `.env` existente al inicio: extrae los valores actuales para no pedirlos de nuevo.

---

## D4 — Validación de claves

| Proveedor | Regex | Endpoint de ping |
|---|---|---|
| Gemini | `^AIzaSy[0-9A-Za-z_-]{33}$` | `GET https://generativelanguage.googleapis.com/v1beta/models?key=KEY` |
| Groq | `^gsk_[0-9A-Za-z]{52,}$` | `GET https://api.groq.com/openai/v1/models` (Bearer) |
| Anthropic | `^sk-ant-[A-Za-z0-9_-]{80,}$` | `GET https://api.anthropic.com/v1/models` (x-api-key) |

Timeout de 5 s en todos los pings.

---

## D5 — Endpoint `/api/models/cloud/status`

```
GET /api/models/cloud/status
```

**Respuesta:**
```json
{
  "gemini":    {"configured": true,  "valid": true,  "error": null},
  "groq":      {"configured": false, "valid": false, "error": null},
  "anthropic": {"configured": true,  "valid": false, "error": "HTTP 401"}
}
```

- `configured`: `bool` — la clave existe en el entorno.
- `valid`: `bool` — la clave pasó el ping HTTP (solo si `configured`).
- `error`: `str | null` — descripción del fallo (formato incorrecto, HTTP 4xx, timeout).

**Cache:** 60 segundos en memoria por proveedor. Evita hammering en cada recarga de página.

---

## D6 — Frontend: disponibilidad unificada

Función `checkAllModelsAvailability()` reemplaza a `checkLocalModelsAvailability()`.

Llama en paralelo a `/api/models/local/status` y `/api/models/cloud/status`.

Para optgroups cloud (`#optgroup-gemini`, `#optgroup-groq`, `#optgroup-anthropic`):
- `!configured` → deshabilitar + tooltip "Sin clave API. Reinstala..."
- `configured && !valid` → deshabilitar + tooltip "La clave no funciona..."
- `configured && valid` → habilitar, sin tooltip.

Para `#optgroup-local`: lógica existente (Ollama down / modelo no descargado).

Si el modelo seleccionado queda deshabilitado, seleccionar automáticamente el primero disponible.

---

## D7 — Anthropic Adapter

- Hereda de `AiProvider`.
- Usa `AsyncAnthropic` del SDK oficial `anthropic`.
- `system_prompt` se pasa al parámetro `system` de la API (separado de `messages`).
- `messages` solo contiene roles `user` / `assistant` (no `system`).
- Manejo de errores `APIError`: 429 → mensaje de rate limit, 401 → clave inválida.
- Streaming vía `client.messages.stream()`.

---

## D8 — Factory routing (orden de prioridad)

1. Tag exacto en `_LOCAL_MODEL_TAGS` → `OllamaAdapter`
2. Empieza por `gemini` → `GeminiAdapter`
3. Empieza por `claude` → `AnthropicAdapter`
4. Contiene `llama` o `mixtral` → `GroqAdapter`
5. Ninguno → `ValueError`

---

## Trade-offs

| Decisión | Alternativa considerada | Razón de la elección |
|---|---|---|
| Cache 60s en memoria | Redis / persistencia | Suficiente para este uso; sin dependencias extra. |
| Ping HTTP en validación | Solo regex | Detecta claves con formato correcto pero revocadas. |
| Opt-in cloud | Wizard obligatorio | Reduce fricción; usuarios sin clave no ven pasos irrelevantes. |
| `LOCAL_MODELS_CATALOG` como nombre principal | Mantener `KNOWN_LOCAL_MODELS` | Más descriptivo; alias retrocompatible para no romper tests viejos. |
