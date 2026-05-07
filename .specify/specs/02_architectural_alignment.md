# Spec 02: Architectural Alignment & Provider Consistency

## Context
The current backend has some logic duplication (like `_get_provider_name` in `ChatService`) and direct dependencies on infrastructure implementations rather than domain abstractions.

## Goals
1.  Unify provider detection to eliminate duplicate logic (Fix A3).
2.  Align with Clean Architecture by using domain interfaces for repositories (Fix Ar1).

## Proposed Changes

### 1. Domain: Provider Base
- Update `AiProvider` interface to include a `name` attribute or a `get_name()` method.
- Each adapter (`GeminiAdapter`, `GroqAdapter`, `OllamaAdapter`) will self-identify.

### 2. Infrastructure: Repository Abstractions
- Create `app/domain/repositories/` with `ConversationRepository` and `MessageRepository` as Abstract Base Classes (ABCs).
- Update `SqlAlchemy` repositories to inherit from these ABCs.

### 3. Application: Service Refactor
- Update `ChatService` to accept `ConversationRepository` and `MessageRepository` (interfaces) instead of specific SqlAlchemy implementations.
- Refactor `ChatService` to use the provider's name directly instead of hardcoded logic.

## Verification
- Verify that chat flow still works.
- Verify that `ChatService` unit tests can now use simple mock repositories more easily.
