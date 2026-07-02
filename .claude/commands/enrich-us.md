---
name: "Enrich Task"
description: Enrich a Geist task stored locally at .claude/us/TAR-XX <Title>.md with implementation-ready technical detail
category: Workflow
tags: [workflow, task, local-us]
---

**Input (obligatorio):** el TAR id, ej. `/enrich-us TAR-02`. Sin él, pregunta al usuario — no adivines.

**Pasos:**
1. Localizar el fichero `.claude/us/TAR-XX *.md` por prefijo
2. Si no existe, decirlo al usuario y sugerir crearlo o usar `/opsx:propose`
3. Si está archivado en `.claude/us/done/`, rechazar y notificar
4. Leer contexto técnico de:
   - `docs/base-standards.md`
   - `docs/adr/` (ADRs relevantes)
   - `.claude/PROYECTO.md` (estado actual)
5. Añadir o reemplazar la sección `## Enhanced` con:
   - Objetivo técnico preciso
   - Tareas atómicas con estimación
   - Dependencias (otros TAR-XX)
   - Riesgos / trade-offs
   - Criterios de aceptación verificables
6. Dejar el resto del fichero intacto

**Estructura del `## Enhanced`:**
```markdown
## Enhanced

### Objetivo técnico
<descripción precisa de qué construir y por qué>

### Tareas atómicas
1. <tarea concreta — 30 min a 2h>
2. ...

### Dependencias
- TAR-XX: <razón>

### Riesgos / trade-offs
- <riesgo>: <mitigación>

### Criterios de aceptación
- [ ] <criterio verificable>
- [ ] mypy --strict pasa sin errores
- [ ] just test pasa
```
