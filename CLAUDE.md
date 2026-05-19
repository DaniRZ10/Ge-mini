# Ge-mini — Claude Code Context

## Proyecto

Python · FastAPI · Alembic · pytest · Ollama · SQLite/PostgreSQL · GGUF Q4  
Autor: Daniel Ríos Zea · DRios@datalsia.com  
IDE: Google Antigravity + Claude Code extension

El contexto completo del proyecto está en `openspec/project.md`. Léelo al inicio de cada sesión.

---

## Metodología activa

SDD con OpenSpec — ciclo expandido obligatorio:

```
/opsx-explore → /opsx-new → /opsx-ff → /opsx-apply → /opsx-verify → /opsx-sync → /opsx-archive
```

Ningún cambio sin artefactos aprobados. Nunca implementes algo que no esté en tasks.md.

---

## Modelo por fase — OBLIGATORIO

Antes de comenzar cada fase muestra este bloque y espera "listo":

```
┌─────────────────────────────────────────────┐
│ 🔄 CAMBIO DE FASE: [nombre]                 │
│ Modelo recomendado : [modelo]               │
│ Temperatura        : [valor]                │
│                                             │
│ Cambia el modelo antes de continuar.        │
│ Escribe "listo" cuando esté seleccionado.   │
└─────────────────────────────────────────────┘
```

| Fase | Modelo | Temp |
|---|---|---|
| Explore · Design · Artefactos | claude-sonnet-4-5 | 0.4 |
| Validación de artefactos | claude-sonnet-4-5 | 0.1 |
| Development `/opsx-apply` | claude-haiku-4-5 | 0.2 |
| QA `/opsx-verify` | claude-sonnet-4-5 | 0.1 |
| Reconciliation | claude-sonnet-4-5 | 0.4 |
| Documentation | claude-haiku-4-5 | 0.3 |
| Sync · Archive | claude-haiku-4-5 | — |

> Opus solo si el change implica rediseño de arquitectura mayor.

---

## Skills activos

**Scope fence:** código del change actual = revisión estricta (bloqueante). Código preexistente = observación (no bloqueante). Separa siempre en Issues / Observaciones.

**TDD:** solo código nuevo. Test primero → falla → mínimo código → pasa.

**Debugging:** causa raíz siempre. Prohibido parches sobre síntomas.

---

## Branching

`main` protegida · `develop` para integración · `feature/opsx-<nombre>` alineada con el change activo · `fix/<desc>` para correcciones.

---

## Documentación

`docs/technical/` → inglés siempre · `docs/manual/` → español
