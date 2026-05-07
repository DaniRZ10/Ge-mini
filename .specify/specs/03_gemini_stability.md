# Spec 03: Gemini Stability & Autodiscovery

## Context
User reports Gemini models failing often. Analysis shows 429 Rate Limits and likely ID mismatches.

## Goals
1.  Implement automatic model discovery from Google AI Studio.
2.  Migrate to official `google-generativeai` SDK.
3.  Improve error handling for 429 (Rate Limit) errors.

## Proposed Changes

### 1. Backend: Model Discovery
- Add endpoint `GET /api/models/gemini` in `app/main.py`.
- Implement `list_models()` in `GeminiAdapter`.

### 2. Backend: SDK Migration
- Install `google-generativeai`.
- Refactor `app/infrastructure/ai/gemini_adapter.py` to use `google.generativeai`.
- Implement exponential backoff for 429 errors.

### 3. Frontend: Dynamic Model List
- Update `static/index.html` to fetch Gemini models on load.
- Populate the `<select>` dynamically.
- Improve error toast/message for 429 errors.

## Verification
- Check if Gemini models list correctly in UI.
- Verify streaming still works with SDK.
- Verify 429 error message is user-friendly.
