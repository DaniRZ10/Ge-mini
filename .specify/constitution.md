# Ge-mini Project Constitution

## 1. Architectural Principles
- **Clean Architecture**: The project must strictly separate Domain, Application, Infrastructure, and API layers.
- **Dependency Rule**: Dependencies must point inwards. Domain cannot depend on Application or Infrastructure.
- **Interfaces (Ports/Adapters)**: External systems (DB, AI APIs) must be accessed via interfaces defined in the Domain or Application layer.

## 2. Security Standards
- **Output Sanitization**: No markdown/HTML content from AI or users shall be rendered without passing through DOMPurify.
- **Authentication**: All API endpoints must require a valid `APP_TOKEN`.
- **Secret Management**: No secrets, keys, or `.env` files shall be included in shared archives or commits.

## 3. Development Workflow (SDD)
- **Spec First**: Every significant change must have a specification in `.specify/specs/`.
- **Atomic Commits**: One task per commit, clearly described.
- **TDD (Test-Driven Development)**: Core business logic must have corresponding unit tests before or during implementation.

## 4. Technical Stack
- **Backend**: FastAPI, SQLAlchemy (Async), Pydantic.
- **Frontend**: Vanilla JS, CSS Variables, HTML5.
- **AI Providers**: Gemini (REST), Groq (SDK/REST), Ollama (REST).

## 5. Coding Standards
- **Type Hinting**: Mandatory for all function signatures.
- **Documentation**: Use Docstrings for complex logic.
- **Errors**: Centralized error handling using FastAPI exception handlers.
