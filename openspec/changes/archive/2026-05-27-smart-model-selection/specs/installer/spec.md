# Spec — smart-model-selection / installer

## ADDED Requirements

### REQ-SMS-01: Hardware-aware model recommendation

**Scenario:** Installer detects RAM and recommends models

WHEN the installer starts  
THEN it reads total system RAM  
AND computes usable RAM as (total − 2 GB)  
AND filters the 11-model catalog to models with `ram_gb <= usable`  
AND selects up to 3 representative models (lightest, middle, heaviest eligible)  
AND marks them as recommended (`[*]`) in the selection table

---

### REQ-SMS-02: Expanded local model catalog

**Scenario:** 11 models available for selection

WHEN the installer presents the local model menu  
THEN it shows all 11 catalog entries with name, category, RAM requirement, and status  
AND status is one of: `[OK]` installed, `[*]` recommended, `[!]` exceeds RAM, `[ ]` available

---

### REQ-SMS-03: Custom Ollama tags

**Scenario:** User enters custom model tags after catalog selection

WHEN the installer finishes catalog selection  
THEN it prompts the user for additional Ollama tags (optional, Enter to finish)  
AND for each tag entered, runs `ollama pull <tag>`  
AND adds successfully pulled tags to the installed set

---

### REQ-SMS-04: Cloud opt-in

**Scenario:** Cloud wizard is optional

WHEN the installer reaches the cloud step  
THEN it asks the user "¿Quieres configurar modelos en la nube? (s/N)"  
AND if the user answers "N" or Enter, skips the cloud wizard entirely  
AND writes `.env` with only `OLLAMA_BASE_URL`

---

### REQ-SMS-05: Existing .env partial respect

**Scenario:** Re-installation skips already-configured keys

WHEN the installer runs and `.env` already exists  
THEN it reads and preserves existing `GEMINI_API_KEY`, `GROQ_API_KEY`, `ANTHROPIC_API_KEY`  
AND does not ask for keys that are already configured  
AND regenerates `.env` with the union of old and new values

---

### REQ-SMS-06: Anthropic provider in installer

**Scenario:** User configures Anthropic Claude

WHEN the user selects provider 3 (Anthropic) in the cloud wizard  
THEN the installer shows format hint (`sk-ant-` + 80+ chars)  
AND shows a cost warning for Claude Opus  
AND validates format with regex before attempting ping  
AND pings `https://api.anthropic.com/v1/models` with headers `x-api-key` and `anthropic-version`  
AND writes `ANTHROPIC_API_KEY` to `.env` if valid (or on user confirmation)

---

### REQ-SMS-07: Welcome CLI message

**Scenario:** Installer shows onboarding before step 1

WHEN the installer starts  
THEN it displays a welcome banner explaining the 5 installation steps  
AND shows detected RAM  
AND before any interactive prompt

---

## ADDED Requirements — Backend

### REQ-SMS-08: Cloud status endpoint

**Scenario:** Frontend queries cloud provider status

WHEN `GET /api/models/cloud/status` is called  
THEN the endpoint returns a JSON object with keys `gemini`, `groq`, `anthropic`  
AND each value has fields `configured` (bool), `valid` (bool), `error` (str or null)  
AND the response always returns HTTP 200  
AND results are cached 60 seconds per provider in memory

### REQ-SMS-09: Anthropic adapter

**Scenario:** Sending a message via Claude

WHEN a request arrives with a `claude-*` model  
THEN `AnthropicAdapter.send_message()` calls `client.messages.create()`  
AND passes `system` prompt as a top-level field (not in `messages`)  
AND transforms history to `[{"role": "user"|"assistant", "content": "..."}]`  
AND on `APIError` 429 returns a rate-limit message  
AND on `APIError` 401 returns an invalid-key message

### REQ-SMS-10: Factory routing for Claude

**Scenario:** Factory routes claude-* models to AnthropicAdapter

WHEN `get_provider()` receives a model ID starting with `claude`  
THEN it returns an `AnthropicAdapter` instance  
AND raises `ValueError` if `ANTHROPIC_API_KEY` is not set

---

## ADDED Requirements — Frontend

### REQ-SMS-11: Anthropic optgroup in UI

**Scenario:** Claude models appear in model selector

WHEN the page loads  
THEN the model selector contains an `<optgroup id="optgroup-anthropic">` with 3 Claude options  
AND the local optgroup has 11 entries matching the catalog  
AND all cloud optgroups have unique IDs (`optgroup-gemini`, `optgroup-groq`, `optgroup-anthropic`)

### REQ-SMS-12: Unified availability check

**Scenario:** Cloud options disabled without valid key

WHEN `checkAllModelsAvailability()` runs  
THEN it calls both `/api/models/local/status` and `/api/models/cloud/status` in parallel  
AND disables all options in a cloud optgroup if `!configured`  
AND disables all options in a cloud optgroup if `configured && !valid`  
AND adds a descriptive tooltip to disabled cloud options  
AND if the selected model becomes disabled, auto-selects the first available option
