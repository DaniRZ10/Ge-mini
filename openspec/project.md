# Ge-mini — Contexto del Proyecto

## Identificación

- **Nombre:** Ge-mini
- **Autor:** Daniel Ríos Zea · DRios@datalsia.com
- **Stack:** Python · FastAPI · Alembic · pytest · Ollama · SQLite / PostgreSQL · GGUF Q4
- **Hardware:** Agnóstico. Sin restricciones de hardware hardcodeadas. Pensado para escalar a distintos equipos.
- **Modelos:** Cualquier modelo soportado por Ollama en formato GGUF. Selección en tiempo de ejecución.
- **IDE:** Google Antigravity con agente Claude Sonnet.
- **Outputs:** Archivos `.md` estructurados para Gamma. Artefactos de investigación, no código de producción.

---

## Metodología: SDD con OpenSpec — Ciclo Expandido

**Principio fundamental:** Ningún cambio sin propuesta aprobada. El agente no implementa nada que no tenga artefactos previos.

### Ciclo completo

/opsx-explore → /opsx-new → /opsx-continue | /opsx-ff → /opsx-apply → /opsx-verify → /opsx-sync → /opsx-archive

### Comandos y cuándo usarlos

| Comando | Cuándo usarlo |
|---|---|
| `/opsx-explore` | Antes de crear nada. Investigar, diagramar, cuestionar. No implementa. |
| `/opsx-new` | Crear el change. Muestra plantilla del primer artefacto y para. |
| `/opsx-continue` | Crear artefactos uno a uno en orden de dependencias. |
| `/opsx-ff` | Cuando la idea está clara. Genera todos los artefactos de una vez. |
| `/opsx-apply` | Implementar las tareas de tasks.md checkbox a checkbox. |
| `/opsx-verify` | Auditoría post-implementación en 3 dimensiones antes de archivar. |
| `/opsx-sync` | Fusionar los deltas con los specs canónicos en `openspec/specs/`. |
| `/opsx-archive` | Cerrar el change. Lo mueve a `archive/YYYY-MM-DD-<nombre>/`. |

### Artefactos de un change (secuencia obligatoria)

openspec/changes/<nombre>/
├── proposal.md       ← Por qué. Motivo, capacidades afectadas, impacto.
├── specs/
│   └── <capability>/
│       └── spec.md   ← Qué exactamente. Formato: Requirement + Scenario WHEN/THEN/AND.
├── design.md         ← Cómo. Decisiones técnicas, trade-offs, goals/non-goals.
└── tasks.md          ← Pasos de implementación con checkboxes. Se deriva de specs + design.

Los specs dentro de un change son **deltas**, no reemplazos. Usan:
- `## ADDED Requirements` — requisitos nuevos
- `## MODIFIED Requirements` — cambios a requisitos existentes
- `## REMOVED Requirements` — requisitos eliminados

Los specs canónicos del proyecto viven en `openspec/specs/` y se actualizan con `/opsx-sync`.

### Las 7 fases del pipeline (workflow a respetar)

1. **Design** — Crear artefactos. Pedir aprobación explícita antes de avanzar.
2. **Development** — Implementar tasks.md. Solo lo que está en los artefactos aprobados.
3. **QA** — Verificar que el código cumple los specs con `/opsx-verify`.
4. **Reconciliation** — Actualizar specs para reflejar lo que realmente se construyó. El código es la verdad.
5. **Documentation** — Generar `docs/technical/` en inglés y `docs/manual/` en español.
6. **User Review** — El usuario revisa. Cambios funcionales → fase 1. Cambios de implementación → fase 2.
7. **Cleanup** — `/opsx-sync` + `/opsx-archive`.

---

## Estrategia de modelos por fase

| Fase | Agente | Modelo | Motivo |
|---|---|---|---|
| Design / Reconciliation | spec-designer | Claude Sonnet 4.6 (Thinking) | Razonamiento abierto, decisiones arquitectónicas |
| Validación de artefactos | spec-validator | Gemini 3.1 Pro (High) | Máxima consistencia, revisión sin creatividad |
| Development | spec-developer | Gemini 3.5 Flash (High) | Ejecución estructurada, rápido |
| QA | spec-qa | Gemini 3.1 Pro (High) | Razonamiento sobre cumplimiento de specs |
| Documentation | spec-documenter | Gemini 3.5 Flash (Medium) | Trabajo por plantilla |
| Sync / Archive | spec-orchestrator | Gemini 3.5 Flash (Medium) | Mecánico puro |

> Claude Opus 4.6 (Thinking) solo si el change implica 
> rediseño de arquitectura mayor.

---

## Skills del agente (guidelines de comportamiento)

### 1. TDD estricto (solo código nuevo)

Para todo código nuevo o modificado en el change actual:
1. Escribir el test primero
2. Verificar que falla
3. Escribir el mínimo código para que pase
4. Verificar que pasa

**No aplica a código preexistente** que no se haya tocado en este change.

### 2. Debugging sistemático

Ante cualquier bug:
1. Reproducir el error de forma consistente
2. Trazar la ruta de ejecución hasta el origen
3. Identificar la causa raíz (no el síntoma)
4. Diseñar el fix para la causa raíz
5. Aplicar y verificar

Prohibido: parches sobre síntomas, `try/except` que engullen errores sin tratarlos.

### 3. Scope fence (valla de alcance)

- **Código del change actual** (nuevo o modificado): revisión estricta. Cualquier problema es bloqueante.
- **Código preexistente** (no tocado en este change): modo observación. Se anota pero no bloquea el avance.

El agente separa siempre los hallazgos en:
- **Issues** → código del change, bloqueantes
- **Observaciones** → código preexistente, no bloqueantes

---

## Patrones de código

- Sin over-engineering.
- Python limpio con type hints en todas las funciones.
- Sin dependencias innecesarias.
- Legibilidad sobre optimización prematura.
- Arquitectura escalable pensada para múltiples equipos.
- Testing con pytest. Cobertura obligatoria en funciones críticas de medición y benchmark.

---

## Branching strategy

| Rama | Propósito | Reglas |
|---|---|---|
| `main` | Producción | Protegida. Solo merge via PR aprobado. |
| `develop` | Integración | Base para features y fixes. |
| `feature/opsx-<nombre>` | Features | Alineada con el nombre del change OpenSpec activo. |
| `fix/<descripción>` | Fixes | Para correcciones puntuales. |

---

## Estructura de documentación

docs/
├── technical/    ← Documentación técnica. Siempre en inglés. Arquitectura, APIs, decisiones.
└── manual/       ← Documentación de usuario. En español. Guías, setup, troubleshooting.

---

## Outputs y formato Gamma

Cada informe de investigación se entrega como archivo `.md` estructurado para importar en Gamma.
- Tema: `stardust`
- Dimensiones: `16x9`
- Imágenes: `pictographic` · estilo `lineArt`
- Footer: Daniel Ríos Zea · DRios@datalsia.com · Serie Ge-mini
