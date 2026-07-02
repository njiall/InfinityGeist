# Geist — Claude Code Context

Lee `docs/base-standards.md` como fuente de verdad antes de hacer cualquier trabajo.

## Branch Discipline (OBLIGATORIO)

Antes de escribir código para una tarea:
1. Comprobar rama actual: `git branch --show-current`
2. Si estás en `main`, crear la rama de feature PRIMERO: `git checkout -b feature/TAR-XX-<short-name>`
3. Nunca commitear código de implementación directamente a `main`

Esta comprobación es obligatoria al inicio de cada `/opsx:apply`, antes de tocar cualquier fichero.

---

## Referencias clave

- [docs/base-standards.md](docs/base-standards.md) — stack, principios, convenciones de código
- [docs/adr/](docs/adr/) — Architecture Decision Records activos
- [.claude/PROYECTO.md](.claude/PROYECTO.md) — estado actual del proyecto y decisiones tomadas
- [.claude/us/](.claude/us/) — tareas y user stories activas (prefijo TAR-XX)
