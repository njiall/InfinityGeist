---
name: "Update Docs"
description: Identify and update technical documentation based on implemented changes in Geist
category: Workflow
tags: [workflow, docs, documentation]
---

Identifica y actualiza la documentación técnica de Geist tras implementar cambios.

**Documentos a considerar:**
- `docs/base-standards.md` — nuevas convenciones, cambios de stack
- `docs/adr/ADR-XXX-*.md` — nuevas decisiones arquitectónicas
- `.claude/PROYECTO.md` — estado de fases, ADRs activos
- `CLAUDE.md` — si cambian las referencias clave

**Reglas:**
- Documentación técnica en **inglés** (ADRs, base-standards)
- `.claude/PROYECTO.md` en **español** (contexto de sesión)
- Proponer cambios al usuario antes de aplicarlos a `docs/`
- Actualizar la tabla de estado de fases en PROYECTO.md al completar una fase
- Al crear un nuevo ADR, seguir la estructura de `docs/adr/ADR-002-*.md`
