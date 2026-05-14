## 1. Preparación del entorno

- [x] 1.1 Confirmar en el `.venv` actual que `pip install -r requirements.txt` instala `google-genai` y que `python -c "from google import genai; from google.genai import types, errors; print(genai.__version__)"` no falla
- [x] 1.2 Validar empíricamente los nombres de atributos asumidos (`m.name`, `m.display_name`, `m.supported_actions`, `chunk.text`, `errors.APIError.code`) con un script descartable y, si alguno difiere, anotar el ajuste en `design.md` antes de codificar

## 2. Migración de `GeminiAdapter`

- [x] 2.1 Reescribir las importaciones de `app/infrastructure/ai/gemini_adapter.py` para usar `from google import genai` y `from google.genai import types, errors`, y eliminar `from google.api_core import exceptions, retry` y `import asyncio`
- [x] 2.2 Sustituir `genai.configure(api_key=...)` por `self._client = genai.Client(api_key=api_key)` en `__init__`
- [x] 2.3 Reescribir `_prepare_history` para devolver `list[types.Content]` con `Part.from_text(text=...)`, mapeando `user`→`user` y resto→`model`
- [x] 2.4 Reescribir `list_models` usando `await self._client.aio.models.list()` (iterando el `AsyncIterator`), filtrando por `"generateContent" in (m.supported_actions or [])` y conservando el formato `{"id": m.name.split("/")[-1], "name": m.display_name}`
- [x] 2.5 Reescribir `send_message` con `await self._client.aio.models.generate_content(model=model_id, contents=history+[user_turn], config=...)`, donde `config` es `types.GenerateContentConfig(system_instruction=self.system_prompt)` sólo si `self.system_prompt` no es vacío, y devolver `response.text`
- [x] 2.6 Reescribir `send_message_stream` como `async for chunk in await self._client.aio.models.generate_content_stream(model=model_id, contents=..., config=...): if chunk.text: yield chunk.text`
- [x] 2.7 Reemplazar el manejo de `exceptions.ResourceExhausted` por `except errors.APIError as e: if e.code == 429: ...` en `send_message` y `send_message_stream`, manteniendo los textos exactos de error definidos en el spec
- [x] 2.8 Verificar que la firma pública (`name`, `list_models`, `send_message`, `send_message_stream`) y los retornos siguen siendo idénticos a los anteriores

## 3. Logging y documentación

- [x] 3.1 En `app/core/logging.py:16` cambiar `logging.getLogger("google.generativeai")` por `logging.getLogger("google.genai")`
- [x] 3.2 En `README.md` línea 80 cambiar `- **IA Cloud:** SDK Oficial de Google Generative AI + Groq SDK.` por ``- **IA Cloud:** SDK `google-genai` (Google Gen AI SDK) + Groq SDK.``

## 4. Verificación

- [x] 4.1 Ejecutar `pytest` y confirmar que toda la suite sigue verde sin tocar tests
- [x] 4.2 Ejecutar `python -c "import app.infrastructure.ai.gemini_adapter"` y confirmar que no hay imports residuales de `google.generativeai` ni `google.api_core`
- [x] 4.3 `grep -rn "google.generativeai\|google-generativeai\|google.api_core" app README.md` debe devolver cero coincidencias
- [ ] 4.4 Con un `GEMINI_API_KEY` real: arrancar `uvicorn app.main:app`, comprobar que `/api/models` devuelve modelos Gemini, que `/api/chat` con un modelo Gemini responde, y que `/api/stream` emite chunks visibles en el frontend
- [ ] 4.5 Validar manualmente el camino de cuota: forzar un 429 (modelo restringido o spam controlado) y confirmar el texto exacto definido en el spec tanto para `send_message` como para `send_message_stream`

## 5. Cierre

- [ ] 5.1 Hacer commits atómicos: (a) migración del adaptador, (b) logger, (c) README
- [x] 5.2 Ejecutar `openspec validate migrate-to-google-genai-sdk --strict` y dejar el cambio listo para `/opsx:archive`
