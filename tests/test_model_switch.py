"""
SPEC 1 — Model Switch Before Response
======================================
Tests para verificar que el sistema "sella" el modelo en el momento del
dispatch (get_provider), no en el momento de la recepción de la respuesta.

ARQUITECTURA RELEVANTE (detectada en TASK-01):
- ChatService.start_chat() llama a self.provider_factory.get_provider(model_id)
  en la línea 24, antes de cualquier await. El objeto provider capturado en
  esa variable local es el que maneja toda la request hasta completarse.
- No existe un "modelo activo global" en el backend: el model_id llega por
  parámetro en cada request. El concepto de "switch" se modela en los tests
  mediante SwitchableFactory, que es una factory con estado mutable.

NOTA SOBRE SESIONES SQLAlchemy:
  ChatService.start_chat() usa dos bloques `async with self.session.begin()` con
  un execute() en medio (línea 34: get_by_conversation). Esto activa el autobegin
  implícitamente. Para evitar el InvalidRequestError al llamar al segundo begin(),
  los tests inyectan la factory a través del override del cliente HTTP, que crea
  una sesión nueva por cada request (exactamente como producción).

ESTRATEGIA DE MOCK:
- SwitchableFactory: fábrica con estado mutable que simula el "modelo activo".
- ControllableProvider: provider con call_log y on_send_hook para introspección.
- Se usa el fixture `client` con dependency_override de get_chat_service para
  inyectar la SwitchableFactory en el ChatService sin tocar producción.
"""
import pytest

import httpx

from app.api.dependencies import get_chat_service
from app.infrastructure.database.repositories import (
    SqlAlchemyConversationRepository,
    SqlAlchemyMessageRepository,
)
from app.application.services.chat_service import ChatService
from tests.conftest import (
    ControllableProvider,
    SwitchableFactory,
    TestSessionLocal,
)


# ─────────────────────────────────────────────────────────────────────────────
# HELPERS LOCALES
# ─────────────────────────────────────────────────────────────────────────────

def _make_override(factory: SwitchableFactory):
    """
    Genera un dependency override para get_chat_service que inyecta
    la SwitchableFactory dada. Cada request HTTP recibe una sesión fresca
    (una sesión por request, igual que en producción).
    """
    async def _override():
        async with TestSessionLocal() as session:
            conv_repo = SqlAlchemyConversationRepository(session)
            msg_repo = SqlAlchemyMessageRepository(session)
            yield ChatService(session, conv_repo, msg_repo, factory)

    return _override


# ─────────────────────────────────────────────────────────────────────────────
# CASO 1.1 — Switch durante request en vuelo
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_1_1_model_sealed_at_dispatch_not_at_response(
    client, provider_a, provider_b
):
    """
    DADO que el modelo activo es A y se despacha una request
    CUANDO el modelo cambia a B durante la ejecución de send_message (en vuelo)
    ENTONCES la respuesta proviene de A
    Y el sistema no llama a B para esta request

    Mecánica: on_send_hook de provider_a ejecuta el switch a provider_b
    DENTRO de send_message, simulando que el cambio ocurre mientras A procesa.
    Como provider_obj ya está capturado en la variable local de start_chat,
    el switch en la factory no afecta a esta request.
    """
    factory = SwitchableFactory(initial_provider=provider_a)

    # El hook simula: "mientras A responde, el usuario cambia a B"
    provider_a.on_send_hook = lambda: factory.switch_to(provider_b)

    from app.main import app
    app.dependency_overrides[get_chat_service] = _make_override(factory)

    try:
        response = await client.post(
            "/api/chat", json={"message": "Hola", "model": "model-a"}
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 200
    data = response.json()

    # La respuesta debe venir de A (el provider sellado al momento del dispatch)
    assert data["response"] == "Respuesta del modelo A"
    assert data["provider"] == "provider_a"

    # A fue llamado exactamente una vez
    assert len(provider_a.call_log) == 1
    assert provider_a.call_log[0][0] == "send_message"

    # B no fue llamado en absoluto (el switch llegó después del dispatch)
    assert len(provider_b.call_log) == 0

    # La factory ahora apunta a B (el switch sí ocurrió en la factory)
    assert factory.get_provider("any") is provider_b


# ─────────────────────────────────────────────────────────────────────────────
# CASO 1.2 — Switch justo antes del dispatch
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_1_2_switch_before_dispatch_uses_new_model(
    client, provider_a, provider_b
):
    """
    DADO que el modelo activo es A
    CUANDO el modelo cambia a B ANTES de que se llame a start_chat
    ENTONCES la request se envía a B (el cambio llegó antes del dispatch)
    Y no se produce ninguna llamada a A
    """
    factory = SwitchableFactory(initial_provider=provider_a)

    # Switch ANTES del dispatch — el usuario cambia de modelo antes de enviar
    factory.switch_to(provider_b)

    from app.main import app
    app.dependency_overrides[get_chat_service] = _make_override(factory)

    try:
        response = await client.post(
            "/api/chat", json={"message": "Pregunta", "model": "model-b"}
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 200
    data = response.json()

    # La respuesta debe venir de B
    assert data["response"] == "Respuesta del modelo B"
    assert data["provider"] == "provider_b"

    # B fue llamado, A no
    assert len(provider_b.call_log) == 1
    assert len(provider_a.call_log) == 0


# ─────────────────────────────────────────────────────────────────────────────
# CASO 1.3 — Switches múltiples rápidos sin requests de por medio
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_1_3_rapid_switches_resolve_to_last_active_model(
    client, provider_a, provider_b, provider_c
):
    """
    DADO que se cambia A → B → C en rápida sucesión sin requests de por medio
    CUANDO se despacha una request
    ENTONCES la request va al modelo C (el último activo)
    Y no hay llamadas residuales a A ni B
    """
    factory = SwitchableFactory(initial_provider=provider_a)

    # Switches rápidos: A → B → C (sin requests entre medias)
    factory.switch_to(provider_b)
    factory.switch_to(provider_c)

    from app.main import app
    app.dependency_overrides[get_chat_service] = _make_override(factory)

    try:
        response = await client.post(
            "/api/chat", json={"message": "Test rápido", "model": "model-c"}
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 200
    data = response.json()

    # Solo C responde
    assert data["response"] == "Respuesta del modelo C"
    assert data["provider"] == "provider_c"

    # C fue llamado exactamente una vez
    assert len(provider_c.call_log) == 1

    # A y B no recibieron ninguna llamada
    assert len(provider_a.call_log) == 0
    assert len(provider_b.call_log) == 0


# ─────────────────────────────────────────────────────────────────────────────
# CASO 1.4a — Switch ANTES del dispatch con modelo local caído → va a CLOUD
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_1_4a_switch_before_dispatch_avoids_local_down(
    client, local_down_provider, cloud_provider
):
    """
    DADO que el modelo activo es LOCAL y está caído
    CUANDO el usuario cambia a CLOUD antes del dispatch
    ENTONCES la request va a CLOUD sin error
    Y el error de LOCAL nunca se produce (local nunca fue llamado)
    """
    factory = SwitchableFactory(initial_provider=local_down_provider)

    # Switch a CLOUD antes del dispatch (el usuario reacciona a tiempo)
    factory.switch_to(cloud_provider)

    from app.main import app
    app.dependency_overrides[get_chat_service] = _make_override(factory)

    try:
        # No debe devolver error 500
        response = await client.post(
            "/api/chat", json={"message": "Consulta cloud", "model": "gemini-model"}
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    assert response.status_code == 200
    data = response.json()

    assert data["response"] == "Respuesta desde la nube"
    assert data["provider"] == "gemini"

    # El provider local nunca fue llamado
    assert len(local_down_provider.call_log) == 0

    # El provider cloud sí fue llamado
    assert len(cloud_provider.call_log) == 1


# ─────────────────────────────────────────────────────────────────────────────
# CASO 1.4b — Switch DESPUÉS del dispatch con modelo local caído → error reportado
# ─────────────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_1_4b_switch_after_dispatch_reports_local_error(
    client, local_down_provider, cloud_provider
):
    """
    DADO que el modelo activo es LOCAL y está caído
    CUANDO el cambio a CLOUD ocurre DESPUÉS del dispatch (dentro de send_message)
    ENTONCES el error de LOCAL se reporta (HTTP 500), no se swallowea

    Mecánica: local_down_provider lanza httpx.ConnectError en send_message.
    El on_send_hook simula el switch a cloud DURANTE la ejecución de local,
    pero el provider ya estaba sellado en provider_obj → el error igualmente
    se propaga porque es local quien ejecuta, no cloud.
    """
    factory = SwitchableFactory(initial_provider=local_down_provider)

    # El hook simula: el usuario cambia a cloud MIENTRAS local ya estaba ejecutando
    local_down_provider.on_send_hook = lambda: factory.switch_to(cloud_provider)

    from app.main import app
    app.dependency_overrides[get_chat_service] = _make_override(factory)

    try:
        response = await client.post(
            "/api/chat", json={"message": "Consulta local", "model": "qwen-model"}
        )
    finally:
        app.dependency_overrides.pop(get_chat_service, None)

    # El error de local DEBE propagarse como 500 — no swallowear ni devolver 200
    assert response.status_code == 500

    # Local intentó ejecutar (y falló con el hook activado)
    assert len(local_down_provider.call_log) == 1

    # Cloud no fue llamado (el switch llegó tarde — dispatch ya había ocurrido)
    assert len(cloud_provider.call_log) == 0
