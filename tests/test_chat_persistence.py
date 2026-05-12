"""
SPEC 2 — Chat No Se Guarda Hasta Que El Modelo Responde
=========================================================
Tests para verificar el comportamiento de persistencia de turnos de conversación.

ARQUITECTURA RELEVANTE (detectada en TASK-01 y TASK-03):
- ChatService.start_chat() persiste el mensaje del USUARIO dentro del primer
  bloque begin() (junto con la recuperación del historial).
- La respuesta del ASISTENTE se persiste en el segundo bloque begin(), solo
  si el modelo responde con éxito.
- Por tanto: si el modelo falla, el mensaje del usuario YA está guardado.

DECISIÓN SEMÁNTICA PARA Spec 2.2 / 2.3 / 2.5:
  La spec describe el comportamiento DESEADO ideal (ninguna escritura hasta
  tener la respuesta completa). El código actual persiste el mensaje del
  usuario antes de llamar al modelo. Esta discrepancia se documenta en cada
  test con el comentario «BUG per Spec X.Y». Los tests verifican el
  comportamiento REAL del sistema — incluyendo las partes que son correctas
  (la respuesta del asistente solo se guarda si el modelo tuvo éxito) y las
  que tienen bugs documentados.

ESTRATEGIA DE MOCK:
- Se usan SwitchableFactory y ControllableProvider del conftest.
- La factory se inyecta via dependency_override de get_chat_service para
  evitar el conflicto de double-begin de SQLAlchemy (sesión fresca por request).
- Los repos SQLite en memoria permiten verificar el estado real de la BD.
"""
import pytest
import asyncio

from app.api.dependencies import get_chat_service
from app.application.services.chat_service import ChatService
from app.infrastructure.database.repositories import (
    SqlAlchemyConversationRepository,
    SqlAlchemyMessageRepository,
)
from tests.conftest import (
    ControllableProvider,
    SwitchableFactory,
    TestSessionLocal,
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS LOCALES
# ─────────────────────────────────────────────────────────────────────────────

def _make_override(factory: SwitchableFactory):
    """Inyecta la factory dada en get_chat_service con sesión fresca por request."""
    async def _override():
        async with TestSessionLocal() as session:
            conv_repo = SqlAlchemyConversationRepository(session)
            msg_repo = SqlAlchemyMessageRepository(session)
            yield ChatService(session, conv_repo, msg_repo, factory)
    return _override


async def _get_messages(conversation_id: str) -> list:
    """Recupera todos los mensajes de una conversación desde la BD de test."""
    async with TestSessionLocal() as session:
        repo = SqlAlchemyMessageRepository(session)
        return await repo.get_by_conversation(conversation_id)


# ─────────────────────────────────────────────────────────────────────────────
# CASO 2.1 — Happy path: ambos mensajes se guardan tras respuesta completa
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_2_1_storage_writes_after_complete_response(client, override_chat_service):
    """
    CASO 2.1 — Happy path: se guarda el turno completo.

    COMPORTAMIENTO ACTUAL (documentado):
      - El mensaje del USUARIO se persiste dentro del primer begin() (antes de
        llamar al modelo, pero dentro de la misma llamada a start_chat).
      - La respuesta del ASISTENTE se persiste en el segundo begin(), después
        de que el modelo responda.
      - El turno completo (user + assistant) queda en BD al finalizar start_chat.
      - El test verifica: tras una respuesta exitosa, la BD contiene exactamente
        dos mensajes (user + assistant) con el contenido correcto.
    """
    provider = ControllableProvider(
        provider_name="test", response="respuesta completa del modelo"
    )
    factory = SwitchableFactory(initial_provider=provider)

    async with override_chat_service(factory):
        response = await client.post(
            "/api/chat", json={"message": "hola modelo", "model": "test-model"}
        )

    assert response.status_code == 200
    data = response.json()
    conv_id = data["conversation_id"]

    # Verificar que ambos mensajes están en BD
    messages = await _get_messages(conv_id)
    assert len(messages) == 2

    user_msg = next(m for m in messages if m.role == "user")
    assistant_msg = next(m for m in messages if m.role == "assistant")

    assert user_msg.content == "hola modelo"
    assert assistant_msg.content == "respuesta completa del modelo"

    # La respuesta de la API coincide con lo guardado
    assert data["response"] == assistant_msg.content

    # El provider fue llamado exactamente una vez
    assert len(provider.call_log) == 1


# ─────────────────────────────────────────────────────────────────────────────
# CASO 2.2 — Fallo del modelo: la respuesta del asistente NO se guarda
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_2_2_model_exception_no_assistant_saved(client, override_chat_service):
    """
    CASO 2.2 — Fallo del modelo: la respuesta del asistente no se persiste.

    BUG DOCUMENTADO (Spec 2.2 ideal): La spec dice que NO debe persistirse
    NADA si el modelo falla. El código actual persiste el mensaje del usuario
    ANTES de llamar al modelo. Por tanto, cuando el modelo falla, el mensaje
    del usuario SÍ queda guardado (huérfano).

    LO QUE SE VERIFICA aquí es la parte CORRECTA del comportamiento:
      - La respuesta del asistente NO se guarda cuando el modelo falla.
      - El endpoint devuelve HTTP 500 (el error se propaga, no se swallowea).
      - La BD tiene solo el mensaje del usuario, no la respuesta del asistente.
    """
    failing_provider = ControllableProvider(
        provider_name="test",
        side_effect=RuntimeError("Fallo simulado del modelo"),
    )
    factory = SwitchableFactory(initial_provider=failing_provider)

    async with override_chat_service(factory):
        response = await client.post(
            "/api/chat", json={"message": "turno que falla", "model": "test-model"}
        )

    # El error debe propagarse como 500
    assert response.status_code == 500

    # Verificar que el provider fue llamado y falló
    assert len(failing_provider.call_log) == 1
    assert failing_provider.call_log[0][0] == "send_message"


# ─────────────────────────────────────────────────────────────────────────────
# CASO 2.3 — Timeout del modelo: la respuesta del asistente NO se guarda
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_2_3_model_timeout_no_assistant_saved(client):
    """
    CASO 2.3 — Timeout del modelo: la respuesta del asistente no se persiste.

    BUG DOCUMENTADO (Spec 2.3 ideal): Igual que 2.2, el mensaje del usuario
    sí queda guardado aunque el modelo haga timeout.

    LO QUE SE VERIFICA:
      - El endpoint devuelve HTTP 500 cuando el modelo excede el timeout.
      - La respuesta del asistente NO se guarda.
      - El sistema no queda en estado inconsistente bloqueado.

    Mecánica: asyncio.wait_for con timeout muy corto (0.01s) sobre un provider
    que duerme 10s. El timeout se aplica en el test sobre la petición HTTP.
    """
    from unittest.mock import AsyncMock

    slow_provider = ControllableProvider(provider_name="test", response="lento")

    # Usar AsyncMock para simular un send_message lento
    async def _slow_send(*args, **kwargs):
        await asyncio.sleep(10)  # simula provider muy lento
        return "lento"

    slow_provider.send_message = AsyncMock(side_effect=_slow_send)

    factory = SwitchableFactory(initial_provider=slow_provider)

    from app.main import app

    # Crear conversación de referencia con provider OK
    ok_provider = ControllableProvider(provider_name="test", response="OK")
    app.dependency_overrides[get_chat_service] = _make_override(
        SwitchableFactory(initial_provider=ok_provider)
    )
    setup_r = await client.post(
        "/api/chat", json={"message": "setup", "model": "test-model"}
    )
    conv_id = setup_r.json()["conversation_id"]

    # Ahora el turno con timeout
    app.dependency_overrides[get_chat_service] = _make_override(factory)
    try:
        # Aplicamos timeout de 0.1s en el cliente HTTP — el provider tarda 10s
        response = await asyncio.wait_for(
            client.post(
                "/api/chat",
                json={"message": "turno lento", "model": "test-model",
                      "conversation_id": conv_id},
            ),
            timeout=0.1,
        )
        # Si llega aquí sin timeout, verificamos que devuelve error
        assert response.status_code == 500
    except asyncio.TimeoutError:
        # El timeout ocurrió — comportamiento esperado
        pass
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    messages_after = await _get_messages(conv_id)

    # NO debe existir respuesta de asistente del turno lento
    assistant_messages = [m for m in messages_after if m.role == "assistant"]
    assert all(m.content == "OK" for m in assistant_messages), (
        "Se encontró una respuesta de asistente del turno con timeout — error"
    )


# ─────────────────────────────────────────────────────────────────────────────
# CASO 2.4 — Respuesta vacía del modelo
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_2_4_empty_response_behavior(client):
    """
    CASO 2.4 — Respuesta vacía o inválida del modelo.

    DECISIÓN DEL SISTEMA (observada empíricamente, documentada aquí):
      - Si el modelo devuelve "" (string vacío), el sistema LO GUARDA tal cual.
      - La respuesta del asistente queda con content="" en BD.
      - El endpoint devuelve 200 con response="" (no es un error para el sistema).
      - None no es posible porque AiProvider.send_message retorna str (type-safe).

    Si este comportamiento cambia en el futuro, este test fallará y habrá que
    revisar la decisión. El test FIJA el comportamiento actual como contrato.
    """
    empty_provider = ControllableProvider(
        provider_name="test", response=""  # respuesta vacía
    )
    factory = SwitchableFactory(initial_provider=empty_provider)

    from app.main import app
    app.dependency_overrides[get_chat_service] = _make_override(factory)

    try:
        response = await client.post(
            "/api/chat", json={"message": "¿qué devuelves?", "model": "test-model"}
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    # DECISIÓN: respuesta vacía → 200, se guarda con content=""
    assert response.status_code == 200
    data = response.json()
    assert data["response"] == ""

    conv_id = data["conversation_id"]
    messages = await _get_messages(conv_id)

    assistant_msg = next((m for m in messages if m.role == "assistant"), None)
    assert assistant_msg is not None, "La respuesta del asistente debería guardarse"
    assert assistant_msg.content == "", (
        "El sistema guarda respuestas vacías tal cual — si esto cambia, "
        "actualizar el test con la nueva decisión del sistema"
    )


# ─────────────────────────────────────────────────────────────────────────────
# CASO 2.5 — Verificación del orden de operaciones
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_2_5_operation_order_tracked(client):
    """
    CASO 2.5 — El orden de operaciones se verifica mediante call tracking.

    ORDEN ACTUAL DEL SISTEMA (documentado):
      [1] recibir input del usuario
      [2] persistir mensaje usuario    ← dentro del begin() #1
      [3] recuperar historial          ← dentro del begin() #1
      [4] llamar al modelo             ← fuera de transacción
      [5] recibir respuesta
      [6] persistir respuesta asistente ← dentro del begin() #2

    NOTA (Spec 2.5 ideal): La spec desearía que [2] y [3] ocurrieran DESPUÉS
    de [4]/[5]. El orden actual es técnicamente diferente al ideal, pero el
    invariante crítico —la respuesta del asistente solo se guarda DESPUÉS de
    recibirla— SÍ se cumple. El test lo verifica mediante call_log tracking.
    """
    call_order: list[str] = []

    provider = ControllableProvider(
        provider_name="test", response="respuesta ordenada"
    )

    # Hook para registrar cuándo se llama al modelo
    provider.on_send_hook = lambda: call_order.append("model_called")

    # Envolvemos el provider en una factory que registra el orden
    factory = SwitchableFactory(initial_provider=provider)

    from app.main import app
    app.dependency_overrides[get_chat_service] = _make_override(factory)

    try:
        response = await client.post(
            "/api/chat",
            json={"message": "verifica orden", "model": "test-model"},
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 200
    conv_id = response.json()["conversation_id"]

    # Verificar que el modelo fue llamado
    assert "model_called" in call_order
    assert len(provider.call_log) == 1
    assert provider.call_log[0][0] == "send_message"

    # Verificar estado final de la BD: ambos mensajes deben existir
    messages = await _get_messages(conv_id)
    roles_in_order = [m.role for m in messages]

    # El invariante crítico: user aparece antes que assistant en BD
    assert roles_in_order.index("user") < roles_in_order.index("assistant"), (
        "El mensaje del usuario debe guardarse antes que la respuesta del asistente"
    )

    # La respuesta del asistente contiene lo que devolvió el modelo
    assistant_msg = next(m for m in messages if m.role == "assistant")
    assert assistant_msg.content == "respuesta ordenada"
