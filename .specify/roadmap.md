# Ge-mini Audit Remediation Roadmap

This document tracks the progress of fixing the vulnerabilities and debt identified in the May 2026 Audit.

## Phase 1: Critical Security & Reliability
- [x] **C1: Local API Key Exposure** (Restrict `.env` usage).
- [x] **C2: XSS Prevention** (Frontend sanitization).
- [ ] **C3: API Authentication** (Token-based auth) - *Postergado por petición del usuario*
- [x] **A1: User Message Persistence** (Fix race condition in `ChatService`).
- [x] **A2: Stream Integrity** (Partial response persistence).

## Phase 2: Architectural Consistency
- [x] **A3: Unified Provider Detection** (Single source of truth for model providers).
- [x] **A5: Google SDK Realignment** (Migrated to official SDK).
- [x] **Ar1: Domain Interfaces** (Defined repository interfaces in Domain).
- [ ] **A6: Ollama System Prompt Fix** (Correct native system role usage).

## Phase 3: Performance & UX
- [ ] **A4: Groq Native Streaming** (Switch to real streaming).
- [x] **M1: Stream Error Handling** (Catch errors inside generators).
- [x] **M4: Structured Logging** (Replace `print` with `logging`).
- [ ] **M5: Configurable System Prompt** (Environment variables & persistence).

## Phase 4: Technical Debt & Hygiene
- [x] **M2: UUID in Domain** (Move ID generation logic).
- [x] **M3/M10: DB Migrations** (Introduce Alembic).
- [x] **M6: Absolute Static Paths** (Fix directory resolution).
- [x] **B1-B8: General Cleanup** (XSS fix, dead code, dependency cleanup).
