---
name: "Commit"
description: Create focused commits following Geist project conventions
category: Workflow
tags: [workflow, git, commit]
---

Crea un commit siguiendo las convenciones del proyecto Geist.

**Convenciones:**
- Formato: `feat(TAR-XX): descripción corta en inglés`
- Tipos: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`
- El ticket TAR-XX es obligatorio para `feat` y `fix`; opcional para otros
- Rama: `feature/TAR-XX-short-description`
- Mensajes de commit en **inglés**

**Pasos:**
1. `git status` — revisar qué hay staged
2. Proponer mensaje de commit siguiendo el formato
3. Si hay múltiples cambios no relacionados, proponer commits separados
4. Ejecutar `just lint && just typecheck` antes de commitear
5. `git commit -m "<mensaje>"`

**Ejemplos válidos:**
```
feat(TAR-02): implement ChromaDB indexing with multilingual-e5-small
fix(TAR-03): apply passage: prefix when indexing chunks
chore: update pre-commit hooks to ruff 0.5
docs(TAR-01): add ADR-002 for pymupdf4llm license decision
test(TAR-03): add golden dataset smoke test for hybrid retrieve
```
