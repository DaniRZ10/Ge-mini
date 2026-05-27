# Tasks — smart-model-selection

## PASO 0: Artefactos OpenSpec
- [x] Crear `openspec/changes/smart-model-selection/proposal.md`
- [x] Crear `openspec/changes/smart-model-selection/design.md`
- [x] Crear `openspec/changes/smart-model-selection/specs/installer/spec.md`
- [x] Crear `openspec/changes/smart-model-selection/tasks.md`

## PASO 1: Dependencias
- [x] Añadir `anthropic` a `requirements.txt`
- [x] Ejecutar `uv pip install -r requirements.txt --quiet`

## PASO 2: Backend — Anthropic adapter
- [x] Crear `app/infrastructure/ai/anthropic_adapter.py`

## PASO 3: Backend — Validadores cloud
- [x] Crear `app/infrastructure/ai/cloud_validators.py`

## PASO 4: Backend — Factory expandido
- [x] Reemplazar `app/infrastructure/ai/factory.py` con catálogo de 11 modelos y routing Anthropic

## PASO 5: Backend — Endpoint cloud status
- [x] Añadir imports `validate_*` a `app/main.py`
- [x] Añadir `import time as _time` a `app/main.py`
- [x] Añadir `_cloud_status_cache` y `_cached_validate()` helper
- [x] Añadir endpoint `GET /api/models/cloud/status`

## PASO 6: Tests
- [x] Crear `tests/test_cloud_validators.py`
- [x] Crear `tests/test_anthropic_adapter.py`
- [x] Crear `tests/test_api_cloud_status.py`
- [x] Modificar `tests/test_factory.py`: actualizar `test_routes_ollama_models` y añadir 2 tests Anthropic

## PASO 7: Frontend
- [x] 7a — Reemplazar optgroups en `static/index.html` (Gemini+ID, Anthropic nuevo, 11 locales, Groq+ID)
- [x] 7b — Reemplazar `checkLocalModelsAvailability` por `checkAllModelsAvailability`
- [x] 7c — Actualizar llamada de inicialización de `checkLocalModelsAvailability()` a `checkAllModelsAvailability()`

## PASO 8: Instalador Linux
- [x] Reemplazar `install.sh` con la versión smart-model-selection

## PASO 9: Instalador Windows
- [x] Reemplazar `tools/_setup/install.ps1` con la versión smart-model-selection

## PASO 10: Documentación
- [x] Actualizar `docs/technical/installer-architecture.md`
- [x] Actualizar `docs/manual/instalacion.md`
- [x] Actualizar `README.md`: tabla de modelos con Anthropic y 11 locales

## Verificación
- [x] `python -m pytest -v` → 60+ passed
- [x] `grep -rn "KNOWN_LOCAL_MODELS" app/ tests/ static/ install.sh tools/_setup/` → solo alias en factory.py
- [x] `python -c "from app.infrastructure.ai.anthropic_adapter import AnthropicAdapter; from app.infrastructure.ai.cloud_validators import validate_anthropic_key; from app.infrastructure.ai.factory import LOCAL_MODELS_CATALOG; print('OK', len(LOCAL_MODELS_CATALOG))"` → `OK 11`
