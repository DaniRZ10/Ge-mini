# Ge-mini Audit Remediation Roadmap

This document tracks the progress of fixing the vulnerabilities and debt identified in the May 2026 Audit.

## Phase 1: Critical Security & Reliability
- [ ] **C2: XSS Prevention** (Frontend sanitization).
- [ ] **C3: API Authentication** (Token-based auth) - *Postergado por petición del usuario*
- [ ] **A1: User Message Persistence** (Fix race condition in `ChatService`).
- [ ] **A2: Stream Integrity** (Partial response persistence).

## Phase 2: Architectural Consistency
- [ ] **A3: Unified Provider Detection** (Single source of truth for model providers).
- [ ] **A5: Google SDK Realignment** (Decide between SDK or pure REST, cleanup README).
- [ ] **Ar1: Domain Interfaces** (Define repository interfaces in Domain).
- [ ] **A6: Ollama System Prompt Fix** (Correct native system role usage).

## Phase 3: Performance & UX
- [ ] **A4: Groq Native Streaming** (Switch to real streaming).
- [ ] **M1: Stream Error Handling** (Catch errors inside generators).
- [ ] **M4: Structured Logging** (Replace `print` with `logging`).
- [ ] **M5: Configurable System Prompt** (Environment variables & persistence).

## Phase 4: Technical Debt & Hygiene
- [ ] **M2: UUID in Domain** (Move ID generation logic).
- [ ] **M3/M10: DB Migrations** (Introduce Alembic).
- [ ] **M6: Absolute Static Paths** (Fix directory resolution).
- [ ] **B1-B8: General Cleanup** (Dead code, pycache, duplicate requirements).
