# Installer Architecture

## Overview

The Ge-mini automated installer is a two-script system (Linux shell + Windows PowerShell) that bootstraps a complete, working instance of the application from zero. No pre-installed software is required beyond a shell.

## Design Goals

| Goal | Rationale |
|---|---|
| Zero prerequisites | Any user can start with a fresh OS and reach a running app |
| Idempotent | Re-running the installer is safe; existing `.env` is preserved |
| Hardware-aware model selection | Recommendations adapt to the machine's RAM |
| Cloud opt-in | Cloud wizard only runs if the user explicitly wants it |
| Three cloud providers | Gemini, Groq, Anthropic — configured individually |
| API key validation (two-phase) | Format regex + live HTTP ping catches revoked keys |
| Always HTTP 200 on status endpoints | Frontend stays responsive even when Ollama is down |

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
┌─────────────────────────────────────────┐
│  Step 3: Local Models (hardware-aware)  │  Detect RAM → recommend → ollama pull
│                                         │  + custom tags prompt
└──────────┬──────────────────────────────┘
           │
           ▼
┌───────────────────────┐
│  Step 4: Cloud (opt-in)│  Ask user → select providers → validate keys → .env
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

## Local Model Catalog (`LOCAL_MODELS_CATALOG`)

Defined in `app/infrastructure/ai/factory.py`. Also exported as `KNOWN_LOCAL_MODELS` for backward compatibility.

| Name | Tag | RAM GB | Category |
|---|---|---|---|
| Qwen Coder 0.5B | `qwen2.5-coder:0.5b` | 2 | Código, ultra ligero |
| Llama 3.2 1B | `llama3.2:1b` | 2 | Chat ligero |
| Qwen Coder 1.5B | `qwen2.5-coder:1.5b` | 3 | Código, ligero |
| Llama 3.2 3B | `llama3.2:3b` | 5 | Chat general |
| Qwen Coder 3B | `qwen2.5-coder:3b` | 5 | Código, equilibrado |
| Phi 3.5 Mini | `phi3.5:latest` | 6 | Razonamiento |
| Mistral 7B Instruct | `mistral:7b-instruct-q4_K_M` | 8 | General, maduro |
| Qwen Coder 7B | `qwen2.5-coder:7b` | 8 | Código, capaz |
| Llama 3.1 8B | `llama3.1:8b` | 8 | Multipropósito |
| Qwen 2.5 14B | `qwen2.5:14b` | 12 | Razonamiento avanzado |
| Mixtral 8x7B | `mixtral:8x7b` | 28 | Top tier MoE |

## Recommendation Algorithm

1. Compute `usable_ram = total_ram − 2` (OS headroom).
2. Filter catalog to models where `ram_gb <= usable_ram` → `eligible` list.
3. If `eligible` is empty → recommend index 0 (lightest model).
4. If `eligible` has 1–3 entries → recommend all.
5. If `eligible` has ≥ 4 entries → select 3 representatives:
   - `eligible[0]` — lightest accessible
   - `eligible[len // 2]` — middle
   - `eligible[-1]` — most capable accessible

Displayed with `[*]` marker; models exceeding RAM show `[!]`.

## Backend: Local Model Status Endpoint

```
GET /api/models/local/status
```

**Response schema:**
```json
{
  "available": ["qwen2.5-coder:3b"],
  "all": ["qwen2.5-coder:0.5b", "llama3.2:1b", "qwen2.5-coder:1.5b",
          "llama3.2:3b", "qwen2.5-coder:3b", "phi3.5:latest",
          "mistral:7b-instruct-q4_K_M", "qwen2.5-coder:7b",
          "llama3.1:8b", "qwen2.5:14b", "mixtral:8x7b"],
  "ollama_running": true
}
```

- Always returns HTTP 200 — the frontend must not assume Ollama is up.
- `available` is the intersection of `LOCAL_MODELS_CATALOG` and the Ollama-installed list.
- The Ollama query uses a 3-second timeout to keep the API responsive.

## Backend: Cloud Status Endpoint

```
GET /api/models/cloud/status
```

**Response schema:**
```json
{
  "gemini":    {"configured": true,  "valid": true,  "error": null},
  "groq":      {"configured": false, "valid": false, "error": null},
  "anthropic": {"configured": true,  "valid": false, "error": "HTTP 401"}
}
```

- `configured`: the env var exists.
- `valid`: the key passed the two-phase validation (format + live HTTP ping).
- `error`: human-readable failure description, or `null` if valid.
- **Cache:** 60 seconds in-memory per provider (`_cloud_status_cache` in `main.py`).

### Validation Details

| Provider | Regex | Ping Endpoint |
|---|---|---|
| Gemini | `^AIzaSy[0-9A-Za-z_-]{33}$` | `GET /v1beta/models?key=KEY` |
| Groq | `^gsk_[0-9A-Za-z]{52,}$` | `GET /openai/v1/models` (Bearer) |
| Anthropic | `^sk-ant-[A-Za-z0-9_-]{80,}$` | `GET /v1/models` (x-api-key) |

Timeout: 5 seconds per ping.

## Frontend: Unified Availability Check

On page load, `checkAllModelsAvailability()` calls both status endpoints in parallel:

- **Local (`#optgroup-local`):** Disables options when Ollama is down or the model is not downloaded. Tooltip explains why.
- **Cloud (`#optgroup-gemini`, `#optgroup-groq`, `#optgroup-anthropic`):**
  - `!configured` → disabled + "Sin clave API..." tooltip
  - `configured && !valid` → disabled + "La clave no funciona..." tooltip
  - `configured && valid` → enabled, no tooltip
- If the selected model becomes disabled, auto-selects the first available option.

## Factory Routing

`AiProviderFactory.get_provider()` priority order:

1. Exact match in `_LOCAL_MODEL_TAGS` → `OllamaAdapter`
2. Starts with `gemini` → `GeminiAdapter`
3. Starts with `claude` → `AnthropicAdapter`
4. Contains `llama` or `mixtral` → `GroqAdapter`
5. No match → `ValueError`

## Security Considerations

- API keys are validated by regex before making HTTP pings.
- The installer never stores keys in memory longer than the session.
- `.env` is in `.gitignore`.
- `install.bat` uses `-ExecutionPolicy ByPass` scoped to the single script invocation, not a system-wide policy change.
- Anthropic Opus cost warning is displayed before asking for the key.
