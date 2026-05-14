# Ge-mini — Project Context for OpenSpec

## Overview

Ge-mini is a minimal, high-performance AI chat interface that allows interaction with multiple AI models (Google Gemini, Groq/Llama, and Local AI via Ollama) from a single unified platform. The project prioritises readability, clean architecture, and scalable multi-team development over premature optimisation.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python · FastAPI · Uvicorn |
| ORM / Migrations | SQLAlchemy 2.0 (Async) · Alembic |
| Database | SQLite (dev) · PostgreSQL (prod-ready) |
| Frontend | Vanilla JS · HTML5 · CSS Variables · Glassmorphism |
| AI Providers | Google Gemini (REST/SDK) · Groq (SDK) · Ollama (REST) |
| Local Models | Any GGUF Q4 model supported by Ollama. Selected at runtime. |
| Testing | pytest · pytest-asyncio |
| Security | DOMPurify (XSS) · python-dotenv |
| Tooling | Alembic · httpx · pydantic-settings |

## Hardware

Agnostic. No hardware constraints are hardcoded. The project is designed to scale across different machines and team setups.

## Architecture

Clean Architecture with strict layer separation:

- `app/domain/` — Pure entities and interfaces (Repository/Provider ports). No external dependencies.
- `app/application/` — Orchestration logic (ChatService). Depends only on domain interfaces.
- `app/infrastructure/` — Concrete implementations (SQLAlchemy repos, AI adapters for Gemini/Groq/Ollama).
- `app/api/` — FastAPI routers and HTTP layer.
- `app/core/` — Global configuration and structured logging.
- `migrations/` — Alembic database versions.
- `static/` — Frontend assets (HTML, CSS, JS).
- `tests/` — pytest test suite.
- `.specify/` — SDD design specifications and project constitution (archived, replaced by OpenSpec).
- `openspec/` — OpenSpec change management.

**Dependency Rule:** Dependencies always point inward. Domain never depends on Application or Infrastructure.

## Development Methodology

SDD (Spec-Driven Development) managed via OpenSpec, profile `core`.

**Change cycle (mandatory):**
1. `/opsx:propose` — Draft and approve a proposal before any work starts.
2. `/opsx:apply` — Implement the approved change task by task.
3. `/opsx:archive` — Archive and close the change once complete.

> No change is implemented without an approved proposal.

## IDE & Agent

- **IDE:** Google Antigravity
- **Agent:** Claude Sonnet

## Coding Standards

- **Type hints:** Mandatory on all function signatures.
- **Docstrings:** Required for complex logic and public interfaces.
- **Error handling:** Centralised via FastAPI exception handlers.
- **Style:** Legibility over premature optimisation. No over-engineering.
- **Commits:** Atomic — one task per commit, clearly described.

## Testing Strategy

- Framework: `pytest` (with `pytest-asyncio` for async code).
- **Coverage is mandatory** for all critical measurement and benchmark functions.
- TDD approach: core business logic must have tests written before or during implementation.

## Outputs

Changes produce `.md` artefacts intended for use with Gamma (presentations, research documents). These are research and planning outputs, not production code.

## Open Roadmap Items

The following items remain open from the May 2026 audit:

- **C3:** API authentication (token-based) — deferred by user request.
- **A6:** Ollama system prompt fix (correct native system role).
- **A4:** Groq native streaming (switch to real streaming).
- **M5:** Configurable system prompt via environment variables.

## Key Constraints

- No secrets, API keys, or `.env` files in commits or shared archives.
- All AI/user markdown output must be sanitised through DOMPurify before rendering.
- External systems (DB, AI APIs) must be accessed only through interfaces defined in the domain/application layer.
