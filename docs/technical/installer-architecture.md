# Installer Architecture

## Overview

The Ge-mini automated installer is a two-script system (Linux shell + Windows PowerShell) that bootstraps a complete, working instance of the application from zero. No pre-installed software is required beyond a shell.

## Design Goals

| Goal | Rationale |
|---|---|
| Zero prerequisites | Any user can start with a fresh OS and reach a running app |
| Idempotent | Re-running the installer is safe; existing state is preserved |
| Interactive model selection | Users choose which local models to download to control disk usage |
| API key validation | Format checks prevent common copy-paste errors |
| Always HTTP 200 on status endpoint | Frontend stays responsive even when Ollama is down |

## Non-Goals

- Automatic OS updates or system package management beyond Ollama
- GPU driver installation
- Docker or container orchestration
- Silent/unattended mode (by design — API keys require user input)

## Component Diagram

```
install.bat / install.sh
        │
        ▼
┌───────────────────────┐
│  Step 1: Python (uv)  │  Install uv → Python 3.12 → .venv → requirements
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Step 2: Ollama       │  Install binary → start service → verify /api/tags
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Step 3: Models       │  Query installed → present menu → ollama pull
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Step 4: API Keys     │  Validate format → write .env
└──────────┬────────────┘
           │
           ▼
┌───────────────────────┐
│  Step 5: DB + Launch  │  alembic upgrade head → uvicorn
└───────────────────────┘
```

## Files

| File | Purpose |
|---|---|
| `install.sh` | Linux/macOS installer (bash) |
| `install.bat` | Windows launcher — delegates to PowerShell |
| `tools/_setup/install.ps1` | Windows installer logic (PowerShell 5+) |
| `start.sh` | Linux quick-launch for subsequent runs |
| `start.bat` | Windows quick-launch for subsequent runs |

## Backend: Local Model Status Endpoint

```
GET /api/models/local/status
```

**Response schema:**
```json
{
  "available": ["qwen2.5-coder:3b"],
  "all": ["qwen2.5-coder:1.5b", "qwen2.5-coder:3b", "phi3.5:latest",
          "mistral:7b-instruct-q4_K_M", "qwen2.5-coder:7b"],
  "ollama_running": true
}
```

- Always returns HTTP 200 — the frontend must not assume Ollama is up.
- `available` is the intersection of `KNOWN_LOCAL_MODELS` and the Ollama-installed list.
- Extra user-pulled models are intentionally excluded from `available`.
- The Ollama query uses a 3-second timeout to keep the API responsive.

## Frontend: Model Availability UI

On page load, `checkLocalModelsAvailability()` calls the status endpoint and:

1. Disables options for models that Ollama reports as not installed.
2. Adds a tooltip explaining why the option is disabled (Ollama down vs. model not downloaded).
3. If the currently selected model was disabled, selects the first available option automatically.

## Known Local Models (`KNOWN_LOCAL_MODELS`)

Defined in `app/infrastructure/ai/factory.py`:

| Name | Tag | Check substring | Size |
|---|---|---|---|
| Qwen 2.5 Coder 1.5B | `qwen2.5-coder:1.5b` | `qwen2.5-coder:1.5b` | ~1.5 GB |
| Qwen 2.5 Coder 3B | `qwen2.5-coder:3b` | `qwen2.5-coder:3b` | ~2.5 GB |
| Phi 3.5 Mini | `phi3.5:latest` | `phi3.5` | ~3.0 GB |
| Mistral 7B Instruct | `mistral:7b-instruct-q4_K_M` | `mistral:7b-instruct` | ~4.8 GB |
| Qwen 2.5 Coder 7B | `qwen2.5-coder:7b` | `qwen2.5-coder:7b` | ~5.2 GB |

The `check` field is a substring used to detect if the model appears in `ollama list` output, which may include quantization suffixes not present in the pull tag.

## Factory Routing

`AiProviderFactory.get_provider()` uses **exact tag matching** against `_LOCAL_MODEL_TAGS` (a set derived from `KNOWN_LOCAL_MODELS`). This eliminates false positives from the previous substring-based approach.

Priority order:
1. Exact match in `_LOCAL_MODEL_TAGS` → `OllamaAdapter`
2. Starts with `gemini` → `GeminiAdapter`
3. Contains `llama` or `mixtral` → `GroqAdapter`
4. No match → `ValueError`

## Security Considerations

- API keys are validated by regex before writing to `.env`.
- The installer never stores keys in memory longer than the session.
- `.env` is in `.gitignore`.
- `install.bat` uses `-ExecutionPolicy ByPass` scoped to the single script invocation, not a system-wide policy change.
