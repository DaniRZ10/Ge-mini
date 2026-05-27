## Why

El instalador `automated-installer` resolvió la fricción técnica de la instalación, pero introdujo tres problemas conceptuales que ahora son visibles:

1. **Lista fija de 5 modelos locales** sin considerar el hardware del usuario.
2. **Modelos cloud obligatorios y siempre visibles** aunque el usuario no tenga claves.
3. **Anthropic no está integrado** como tercer proveedor cloud.

Además, el wizard pide las claves de forma obligatoria. La filosofía correcta: solo configurar lo que vas a usar.

## What Changes

- Mensaje de bienvenida CLI al inicio del instalador.
- Detección de RAM cross-platform.
- Catálogo de modelos locales expandido a 11.
- Recomendación automática de 3 modelos según hardware.
- Tags de Ollama personalizados al final del wizard local.
- Wizard cloud pasa a opt-in.
- Anthropic como tercer proveedor cloud (Opus 4.7, Sonnet 4.6, Haiku 4.5).
- Validación real de claves con ping HTTP.
- `.env` parcial respetado en reinstalaciones.
- Endpoint `GET /api/models/cloud/status`.
- Frontend deshabilita optgroups cloud sin clave válida.

## Capabilities

### New Capabilities
- `hardware-aware-installer`, `cloud-opt-in`, `anthropic-provider`, `cloud-key-validation`, `custom-ollama-tags`.

### Modified Capabilities
- `installer-model-selector`, `local-ai-provider`, `installer-api-keys`, `local-model-availability`.

## Impact

Archivos nuevos: `anthropic_adapter.py`, `cloud_validators.py`, sus tests.
Modificados: `factory.py`, `main.py`, `index.html`, `install.sh`, `install.ps1`, `requirements.txt`, docs.
