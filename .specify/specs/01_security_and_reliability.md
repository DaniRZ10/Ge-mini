# Technical Specification 01: Security & Reliability Core

## Problem Statement
The May 2026 audit identified critical vulnerabilities:
1. **XSS (C2)**: Markdown output is rendered directly using `innerHTML` without sanitization.
2. **Missing Auth (C3)**: API endpoints are public and billable.
3. **Race Conditions (A1/A2)**: Messages are persisted *after* AI calls, leading to data loss on failure.

## Proposed Solutions

### 1. XSS Prevention (DOMPurify)
- **Target**: `static/index.html`.
- **Method**: Load DOMPurify via CDN and wrap all `marked.parse()` calls with `DOMPurify.sanitize()`.
- **Verification**: Attempt to render a message with `<img src=x onerror=alert(1)>` and ensure it is neutralized.

### 2. API Token Authentication
- **Backend**:
    - Add `APP_TOKEN` to `.env`.
    - Create a security dependency in `app/api/dependencies.py` using `secrets.compare_digest`.
    - Apply `Depends(require_token)` to all `/api/` endpoints in `app/main.py`.
- **Frontend**:
    - Update `static/index.html` to include `Authorization: Bearer <token>` in all `fetch` calls.
    - Retrieve token from a simple login prompt or a persistent variable (for now, a config variable).

### 3. Reliable Persistence (Pre-flight Saving)
- **Target**: `app/application/services/chat_service.py`.
- **Refactor**: 
    1. Persist the `user` message immediately upon receiving the request.
    2. Obtain or create the `conversation_id`.
    3. Invoke the AI provider.
    4. Persist the `assistant` reply (or error message) in a `finally` block or post-call.
- **Streaming**: Ensure `save_stream_result` handles partial captures even if the connection drops.

## Verification Plan
- **Automated**:
    - Test that `/api/chat` returns 401 without token.
    - Test that `ChatService.start_chat` persists user message even if `provider.send_message` raises Exception.
- **Manual**:
    - Verify UI renders markdown correctly but blocks scripts.
