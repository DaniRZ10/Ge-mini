# spec-start — Pipeline 7 Fases

Activa el pipeline completo para un change.
Si ya existe .pipeline/status.json, retoma desde
la última fase completada.

## Uso
/spec-start <nombre-del-change>

## Las 7 fases

### Fase 1 — Design [spec-designer + spec-validator]
Modelo: Claude Sonnet 4.6 (Thinking)
- designer crea artefactos del change
- validator revisa (máx 2 iteraciones por issue BLOCKING)
- ⏸ CHECKPOINT: usuario aprueba specs antes de continuar

### Fase 2 — Development [spec-developer]
Modelo: Gemini 3.5 Flash (High)
- developer implementa tasks.md checkbox a checkbox
- TDD + scope fence + debugging sistemático
- ⏸ CHECKPOINT: usuario aprueba implementación

### Fase 3 — QA [spec-qa + spec-developer]
Modelo: Gemini 3.1 Pro (High)
- qa verifica spec-vs-código
- developer corrige si hay issues (máx 3 iteraciones)
- ⏸ CHECKPOINT: usuario aprueba calidad

### Fase 4 — Reconciliation [spec-designer + spec-validator]
Modelo: Claude Sonnet 4.6 (Thinking)
- designer actualiza specs para reflejar lo construido
- el código es la verdad, no el spec original
- validator confirma coherencia

### Fase 5 — Documentation [spec-documenter + spec-validator]
Modelo: Gemini 3.5 Flash (Medium)
- documenter genera docs/technical/ (EN) y docs/manual/ (ES)
- validator chequea consistencia

### Fase 6 — User Review
- ⏸ CHECKPOINT: usuario revisa todo
- Cambios funcionales → vuelve a Fase 1
- Cambios de implementación → vuelve a Fase 2
- Si hay deferred issues: "Hay N issues pendientes, ¿los resolvemos?"

### Fase 7 — Cleanup [spec-orchestrator]
Modelo: Gemini 3.5 Flash (Medium)
- /opsx-sync (fusionar deltas con specs canónicos)
- /opsx-archive (cerrar el change)

## Estado persistente
El estado se guarda en:
openspec/changes/<nombre>/.pipeline/status.json

Si se cierra la sesión, /spec-start <nombre> retoma
donde se dejó.
