## Why

`requirements.txt` ya declara `google-genai` (el nuevo SDK unificado de Google), pero `app/infrastructure/ai/gemini_adapter.py` sigue importando `google.generativeai` (el SDK antiguo, en modo mantenimiento y sin soporte para nuevas capacidades de Gemini). Esta divergencia hace que el adaptador funcione sólo si el SDK antiguo está accidentalmente presente en el entorno y bloquea cualquier evolución hacia features actuales (Gemini 2.5, thinking config, multimodal nativo, etc.). Migrar ahora alinea código y dependencias antes de que el SDK antiguo deje de instalarse.

## What Changes

- **BREAKING (interna):** `GeminiAdapter` deja de depender de `google.generativeai` y pasa a usar `google.genai` (clase `genai.Client` y módulo `genai.types`).
- Reescribir `list_models`, `send_message` y `send_message_stream` sobre la API del nuevo SDK manteniendo idéntica firma pública (`AiProvider`) y semántica observable (mismo formato de respuesta, mismos mensajes de error de cuota, mismo comportamiento de streaming asíncrono).
- Sustituir `genai.configure(api_key=...)` por instanciación de `genai.Client(api_key=...)` guardada en el adaptador.
- Reemplazar las excepciones `google.api_core.exceptions.ResourceExhausted` por las del nuevo SDK (`google.genai.errors.APIError` con detección por `code == 429`).
- Ajustar el filtro de logging en `app/core/logging.py` para silenciar `google.genai` en lugar de `google.generativeai`.
- Actualizar `README.md` para citar el nuevo SDK (`google-genai`) en la sección de tecnologías.

## Capabilities

### New Capabilities
- `gemini-provider`: Define los requisitos observables del proveedor Gemini (listado de modelos, envío de mensaje completo y streaming, manejo de cuota) que `GeminiAdapter` debe cumplir, independientemente del SDK subyacente.

### Modified Capabilities
<!-- No hay specs previas en openspec/specs/; esta es la primera capability. -->

## Impact

- **Código:**
  - `app/infrastructure/ai/gemini_adapter.py` (reescritura completa de las llamadas al SDK).
  - `app/core/logging.py:16` (nombre del logger a silenciar).
- **Dependencias:** ninguna nueva; `requirements.txt` ya lista `google-genai`. Se confirma que `google-generativeai` y `google-api-core` (usado por el adaptador para `exceptions`/`retry`) dejan de ser necesarios.
- **Documentación:** `README.md` (sección "Tecnologías Utilizadas").
- **Tests:** `tests/test_factory.py` y `tests/conftest.py` siguen siendo válidos a nivel de firma; los tests de integración que ejerciten Gemini real deben verificarse manualmente. Los mocks no tocan `google.generativeai` directamente, así que no requieren cambios estructurales.
- **API HTTP / contrato externo:** sin cambios. Los endpoints `/api/chat`, `/api/stream` y `/api/models` mantienen su comportamiento.