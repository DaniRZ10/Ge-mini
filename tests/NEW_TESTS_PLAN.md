# NEW TESTS PLAN — Ge-mini
# Autor: Daniel Ríos Zea | Elaborado por: Antigravity (AI assistant)
# Fecha: 2026-05-12
# Tarea: TASK-01 · Reconnaissance

---

## 1. FRAMEWORK Y CONVENCIONES

### Framework
- **pytest** con el plugin **pytest-asyncio** (`asyncio_mode = auto` en `pytest.ini`).
- Todos los tests asíncronos usan `@pytest.mark.asyncio`.
- El directorio raíz de tests es `tests/` (definido en `pytest.ini`: `testpaths = tests`).

### Convenciones de naming detectadas
- Archivos: `test_<módulo>.py` (snake_case, prefijo `test_`).
- Funciones sueltas: `test_<verbo>_<sujeto>_<resultado>` — ej. `test_start_chat_creates_new_conversation`.
- Clases de agrupación: `class Test<Concepto>:` — usadas en `test_factory.py` y `test_entities.py`.
- Docstrings en cada test describiendo su intención en español.

### Mezcla de estilos
- Los tests de integración HTTP (API) usan funciones sueltas con fixture `client`.
- Los tests unitarios del servicio instancian `ChatService` directamente.
- Los tests de entidades y factory usan clases de agrupación.
- **Decisión para los nuevos tests**: usar funciones sueltas con `@pytest.mark.asyncio`,
  consistentes con `test_chat_service.py`, ya que ambos specs son sobre comportamiento
  del servicio, no sobre la API HTTP.

---

## 2. FIXTURES EXISTENTES (conftest.py)

| Fixture | Scope | Descripción |
|---|---|---|
| `event_loop` | session | Event loop compartido para toda la sesión |
| `setup_database` | function (autouse) | Crea/destruye tablas SQLite en memoria por cada test |
| `db_session` | function | `AsyncSession` directa para tests unitarios |
| `client` | function | `AsyncClient` HTTPX con dependencias FastAPI sobreescritas |

### Clases helper en conftest.py
- **`FakeProvider`**: implementa `AiProvider`, devuelve respuestas predecibles sin red.
- **`FakeProviderFactory`**: fábrica que siempre retorna `FakeProvider`.

### Imports disponibles para reutilización
```python
from tests.conftest import FakeProviderFactory  # ya usado en test_chat_service.py
from app.domain.providers.base import AiProvider
from app.infrastructure.database.repositories import (
    SqlAlchemyConversationRepository, SqlAlchemyMessageRepository
)
from app.application.services.chat_service import ChatService
```

---

## 3. ANÁLISIS DEL CÓDIGO DE PRODUCCIÓN RELEVANTE

### 3.1 Routing de modelos — `app/infrastructure/ai/factory.py`

`AiProviderFactory.get_provider(model_id: str)` selecciona el adapter en el momento
de la llamada. **No hay estado de "modelo activo" en el servicio**: el `model_id` se
pasa como argumento en cada request.

**Implicación para Spec 1 (Model Switch)**:
El sistema no tiene un concepto de "modelo activo global" — el `model_id` se recibe
como parámetro del request HTTP y se pasa directamente a `start_chat(model_id=...)`.
El "sellado en el momento del dispatch" ocurre de forma natural porque `get_provider`
se llama al inicio de `start_chat`, antes de cualquier await que pueda intercalar un
cambio. Lo que hay que testear es que la referencia al provider capturada al inicio de
`start_chat` es la que se usa para procesar la respuesta, **aunque una llamada posterior
cambie el proveedor activo en la factory**.

Escenario real: si la factory fuera stateful (guardase el último modelo seleccionado),
podría haber un race condition en un servidor concurrente. Los tests deben verificar
este invariante incluso si hoy pasa trivialmente, para fijar el comportamiento.

### 3.2 ChatService — `app/application/services/chat_service.py`

Método principal: `start_chat(message_content, model_id, conversation_id)`

```
Línea 24: provider_obj = self.provider_factory.get_provider(model_id)  ← DISPATCH
Línea 31: await self._save_message(..., "user", ...)                    ← GUARDA USUARIO
Línea 37: reply_content = await provider_obj.send_message(...)          ← LLAMA MODELO
Línea 41: await self._save_message(..., "assistant", reply_content, ...) ← GUARDA RESPUESTA
```

**BLOCKER CRÍTICO para Spec 2 (Chat Persistence)**:
El comportamiento actual del `start_chat` **NO cumple la spec**:
- El mensaje del **usuario se persiste ANTES de llamar al modelo** (línea 31).
- Solo la respuesta del asistente se guarda después.
- Según la Spec 2, "el turno de conversación NO debe persistirse hasta que la respuesta
  esté completa". Hoy el mensaje del usuario queda guardado aunque el modelo falle.

**DECISIÓN REQUERIDA** — ver sección 5 (BLOCKERS).

### 3.3 OllamaAdapter — `app/infrastructure/ai/ollama_adapter.py`

- `send_message`: Hace HTTP POST a `http://localhost:11434/api/chat`. Captura
  `Exception` internamente y devuelve string de error en lugar de lanzar — esto
  es un antipatrón para testear correctamente (el servicio no ve la excepción).
- `send_message_stream`: Captura `httpx.ConnectError` y `Exception` y los emite
  como texto en el stream, en lugar de lanzar excepciones.

**Implicación**: Para testear Caso 1.4 (modelo local caído), hay que mockear el
provider directamente, no la conexión HTTP, porque el adapter ya "swallowea" los
errores de conexión y los convierte en strings.

### 3.4 AiProvider base — `app/domain/providers/base.py`

Interface abstracta con:
- `name: str` (property abstracta)
- `send_message(message, history, model_id) -> str`
- `send_message_stream(message, history, model_id) -> AsyncIterator[str]`

Los tests crearán subclases de `AiProvider` directamente (sin usar la factory real)
para controlar el comportamiento exacto en cada caso.

---

## 4. ESTRATEGIA DE MOCK

### Para Spec 1 (Model Switch Before Response)

**Approach**: Crear providers falsos con comportamiento controlado, instanciar
`ChatService` directamente (como en `test_chat_service.py`), y simular la factory.

```python
# Mock de factory stateful para simular switch
class SwitchableFactory:
    def __init__(self, initial_provider):
        self._provider = initial_provider

    def switch(self, new_provider):
        self._provider = new_provider

    def get_provider(self, model_id: str):
        return self._provider
```

Para Caso 1.4 (modelo local caído), se necesita un provider que lance
`httpx.ConnectError` o similar en `send_message`.

**No se puede testear concurrencia real** en asyncio sin un executor externo.
Los casos 1.1-1.4 se modelarán como tests síncronos de dispatch-time vs
response-time usando side_effects y AsyncMock:
- Caso 1.1: La factory captura el provider al momento del dispatch. El test verifica
  que el provider llamado es el registrado en el momento de iniciar `start_chat`.
- Caso 1.2: El test llama al método con el provider ya switcehado — trivial.
- Caso 1.3: Solo el último modelo establecido se usa.
- Caso 1.4: El provider local lanza excepción; el test verifica comportamiento.

### Para Spec 2 (Chat Persistence)

**Approach**: Usar un `MessageRepository` mock con `unittest.mock.AsyncMock` y
call tracking para verificar:
- Cuántas veces se llamó `add()`
- En qué orden se llamaron los métodos

```python
from unittest.mock import AsyncMock, MagicMock, call

mock_msg_repo = AsyncMock(spec=MessageRepository)
mock_conv_repo = AsyncMock(spec=ConversationRepository)
```

Para verificar el ORDEN de operaciones (Caso 2.5), se usará un tracker de llamadas:

```python
call_log = []
mock_msg_repo.add.side_effect = lambda msg: call_log.append(("add", msg.role))
provider.send_message.side_effect = lambda *a, **k: call_log.append(("model_call",))
```

---

## 5. BLOCKERS Y AMBIGÜEDADES — REVISAR CON OWNER

### BLOCKER-01 ⚠️ — Comportamiento actual de ChatService viola Spec 2

**Observado en `chat_service.py` línea 31**:
```python
await self._save_message(conversation_id, "user", message_content, ...)
```
Este `_save_message` ocurre **antes** de `await provider_obj.send_message(...)`.

Si el modelo lanza una excepción, el mensaje del **usuario ya quedó persistido**.
Esto contradice Spec 2.2 y 2.3 que dicen "el storage NO recibe ninguna escritura".

**Opciones**:
1. Marcar los casos 2.2 y 2.3 con `@pytest.mark.xfail(reason="BUG: ...")` y reportar.
2. Refactorizar `start_chat` para persistir usuario+asistente juntos (en una sola
   transacción, solo si el modelo respondió bien). **REQUIERE CONFIRMACIÓN DEL OWNER**.

**Por defecto (siguiendo la spec)**: Opción 1 — marcar como xfail, no tocar producción.

### BLOCKER-02 ⚠️ — Spec 2 vs. streaming pathway

El endpoint de streaming (`get_stream_generator`) ya no persiste nada — la persistencia
se delega al caller via `persist_user_message` / `persist_assistant_message`. Solo
el endpoint `/api/chat` (no-stream) usa `start_chat`. Los nuevos tests deben operar
sobre `start_chat` (flujo no-streaming), que es donde está el comportamiento descrito.

### AMBIGÜEDAD-01 — Spec 1: "modelo activo" no es un concepto del backend

En el backend actual, no existe un "modelo activo global". El `model_id` se pasa
en cada request. "Model switch" en la Spec 1 se interpreta como: la factory puede
ser stateful (cambio de provider pre-registrado), y el test debe verificar que el
provider resuelto al inicio de `start_chat` no es reemplazado durante la ejecución.
Esto se testea instanciando providers directamente, sin depender de estado global.

### AMBIGÜEDAD-02 — Spec 2.4: respuesta vacía o None

`AiProvider.send_message` retorna `str`. El sistema actual no valida si el string
está vacío antes de persistir. Si `send_message` devuelve `""` o `None`:
- `""` → se guardaría como respuesta vacía (el campo `content` acepta cualquier string).
- `None` → causaría un error en `Message(content=None)` porque `content: str`.
El test 2.4 debe documentar este comportamiento mediante observación antes de afirmar.

---

## 6. FIXTURES NUEVAS NECESARIAS (para TASK-02)

| Fixture | Descripción | Archivo destino |
|---|---|---|
| `controllable_provider` | Provider con `send_message` configurado vía fixture parameter | `conftest.py` o nuevo |
| `erroring_provider` | Provider que lanza `RuntimeError` en `send_message` | `conftest.py` |
| `timeout_provider` | Provider que hace `asyncio.sleep(largo)` para simular timeout | `conftest.py` |
| `tracking_msg_repo` | `AsyncMock(spec=MessageRepository)` con call order log | `conftest.py` |
| `tracking_conv_repo` | `AsyncMock(spec=ConversationRepository)` con call order log | `conftest.py` |

**DECISIÓN**: Las nuevas fixtures van al `conftest.py` existente para que sean
accesibles desde cualquier archivo de tests. NO se duplican las existentes
(`FakeProvider`, `FakeProviderFactory`, `db_session`, `client`, etc.).

**Nueva dependencia de test necesaria**: `pytest-mock` — añadir a `requirements-test.txt`.
Justificación: ofrece `mocker` fixture con scope control y auto-cleanup, simplifica
`unittest.mock.patch` en contextos async.

---

## 7. ARCHIVOS NUEVOS QUE SE CREARÁN

| Archivo | Tarea |
|---|---|
| `tests/NEW_TESTS_PLAN.md` | Este documento (TASK-01) |
| `tests/test_model_switch.py` | Spec 1, 4 casos (TASK-03) |
| `tests/test_chat_persistence.py` | Spec 2, 5 casos (TASK-04) |
| `requirements-test.txt` | Añadir `pytest-mock` (TASK-02) |

**Archivos modificados**:
| Archivo | Tarea | Cambio |
|---|---|---|
| `tests/conftest.py` | TASK-02 | Añadir fixtures nuevas al final |

**Archivos de producción**: NINGUNO.
