## Context

`GeminiAdapter` (`app/infrastructure/ai/gemini_adapter.py`) implementa `AiProvider` para Gemini. Hoy importa `google.generativeai` (SDK antiguo) aunque `requirements.txt` ya declara `google-genai` (SDK nuevo). Sólo funciona si el SDK viejo queda residualmente instalado. El SDK nuevo unifica la API: cliente único `genai.Client`, configuración por argumentos, errores en `google.genai.errors`, soporte nativo de async y streaming.

El resto del sistema consume `GeminiAdapter` por la interfaz `AiProvider` (`name`, `send_message`, `send_message_stream`) más `list_models`. Único acoplamiento adicional: el filtro de logging en `app/core/logging.py:16`.

## Goals / Non-Goals

**Goals:**
- Reemplazar todas las llamadas a `google.generativeai` por equivalentes en `google.genai` dentro de `GeminiAdapter`, sin cambiar firmas públicas ni semántica observable.
- Conservar el contrato actual de `list_models` (`[{"id", "name"}]` filtrado a modelos que soporten generación de contenido).
- Conservar el streaming asíncrono yieldando los `text` de cada chunk a medida que llegan.
- Mantener el texto exacto del mensaje de cuota (HTTP 429) en `send_message` y `send_message_stream`.
- Apuntar el filtro de logging al nuevo logger (`google.genai`).
- Actualizar `README.md` para reflejar el nombre real del SDK.

**Non-Goals:**
- Adoptar nuevas features del SDK (thinking config, multimodal, function calling, tools).
- Cambiar `AiProvider` o tocar los demás adaptadores (Groq, Ollama).
- Reescribir tests; sólo se ajustarán si algún mock referencia explícitamente módulos del SDK antiguo (no es el caso).

## Decisions

### D1. Cliente único: `genai.Client(api_key=...)` en `__init__`

`google-genai` reemplaza `genai.configure(...)` + `GenerativeModel(...)` por un `Client` explícito. Guardamos `self._client` y lo reusamos en `list_models`, `send_message` y `send_message_stream`.

**Alternativa:** crear el cliente *ad hoc* en cada llamada. Descartado: duplica setup; el cliente es barato de mantener vivo.

### D2. Async real con `client.aio` en lugar de `run_in_executor`

El nuevo SDK expone superficie async nativa bajo `client.aio.models.*`:
- `loop.run_in_executor(None, lambda: list(genai.list_models()))` → iterar `await self._client.aio.models.list()`.
- `await model.generate_content_async(...)` → `await self._client.aio.models.generate_content(model=..., contents=..., config=...)`.
- streaming: `async for chunk in await self._client.aio.models.generate_content_stream(model=..., contents=..., config=...)`.

**Alternativa:** seguir empujando llamadas síncronas a un executor. Descartado: añade overhead y va contra el grano del SDK.

### D3. `system_instruction` por petición vía `types.GenerateContentConfig`

Antes se pasaba al construir `GenerativeModel`; ahora va por petición. Construimos `config` perezosamente: `None` si `self.system_prompt` es vacío, `types.GenerateContentConfig(system_instruction=self.system_prompt)` en caso contrario, reutilizado en `send_message` y `send_message_stream`.

### D4. Historial: `types.Content` + `types.Part.from_text`

`_prepare_history` pasa de dicts `{"role", "parts": [text]}` a `list[types.Content]` con `Part.from_text(text=...)`. Para `send_message` reutilizamos `contents = history + [user_turn]` y una sola llamada a `generate_content`, evitando `chats.create(...)` (no aporta nada aquí).

### D5. Errores: `google.genai.errors.APIError` con detección de 429

`google.api_core.exceptions.ResourceExhausted` desaparece. El nuevo SDK levanta `google.genai.errors.APIError` con atributo `.code` (entero HTTP). Detectamos cuota con `except errors.APIError as e: if e.code == 429: ...`. Textos exactos preservados:
- `send_message`: `"Error: Has agotado tu cuota de Gemini (Rate Limit). Por favor, espera un minuto o prueba con otro modelo."`
- `send_message_stream`: `"Error: Cuota agotada (Rate Limit). Reintenta en un minuto."`

### D6. Reintentos: delegar al SDK

El código actual envuelve cada llamada con `request_options={"retry": retry.Retry(predicate=...)}`. El nuevo SDK no expone ese `request_options` y ya gestiona reintentos transitorios internos. Eliminamos el wrapping manual: para 429 no queremos reintentar (devolver mensaje de cuota), que es el comportamiento efectivo actual.

### D7. Filtro de modelos en `list_models`

SDK antiguo: `m.supported_generation_methods` filtrado por `"generateContent"`. SDK nuevo: `m.supported_actions`. Misma semántica: incluir sólo modelos cuyo `supported_actions` contenga `"generateContent"`; si viene `None`, se omite. `id` se deriva de `m.name.split("/")[-1]`; `display_name` se usa tal cual.

### D8. Logging

`app/core/logging.py:16`: `"google.generativeai"` → `"google.genai"`. Sin cambio de nivel.

### D9. README

`README.md` línea 80: `- **IA Cloud:** SDK Oficial de Google Generative AI + Groq SDK.` → `- **IA Cloud:** SDK \`google-genai\` (Google Gen AI SDK) + Groq SDK.`

## Risks / Trade-offs

- **Riesgo:** nombres de atributo del nuevo SDK podrían diferir (`m.supported_actions` u otros). → **Mitigación:** verificación manual con `python -c "from google import genai; ..."` durante la implementación; ajustar `list_models` antes de cerrar la tarea.
- **Riesgo:** `generate_content_stream` devuelve un awaitable que produce un `AsyncIterator`, no directamente un iterador. → **Mitigación:** cubierto en el spec (escenario de streaming) y aquí (D2) con `async for chunk in await ...`.
- **Trade-off:** se elimina el reintento manual de `ResourceExhausted`. Aceptable: ya era no-op funcional.
- **Trade-off:** README cita el paquete pip en vez del nombre comercial; gana precisión, pierde marketing. Aceptable.

## Migration Plan

1. Verificar en un entorno limpio que `pip install -r requirements.txt` instala `google-genai` y que `import google.genai` funciona.
2. Reescribir `GeminiAdapter` en un commit; correr `pytest` (debe seguir verde sin tocar tests).
3. Actualizar `app/core/logging.py` y `README.md` en commits atómicos separados.
4. Verificación manual end-to-end con `GEMINI_API_KEY` real: `/api/models` devuelve modelos Gemini, `/api/chat` con modelo Gemini responde, `/api/stream` emite chunks.
5. **Rollback:** revertir los commits. Reinstalar `google-generativeai` manualmente (la versión previa de `requirements.txt` lo lleva implícito en el registro git).
