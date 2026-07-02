# PROYECTO — Geist

Contexto persistente del proyecto para Claude Code. Pensado para leerse en cada sesión sin tener que redescubrir nada. Es **resumen y decisiones tomadas**, no documentación exhaustiva — para detalle, sigue los enlaces.

## Producto

Sistema RAG para consultar las reglas de Infinity N5 (wargame de miniaturas de Corvus Belli). API-first, bot de Telegram (@geistBot), bilingüe ES/EN. Proyecto personal no monetizado de Rubén.

- Precisión literal sobre prosa fluida: devuelve fragmentos exactos con cita de página
- Sin capa LLM en el MVP (diferido a F9 por ADR-001)
- Fuentes en scope: reglas N5, annexes, Quickstart Modiphius (gratuito)

## Stack

| Capa            | Tecnología                                                     |
|-----------------|----------------------------------------------------------------|
| API             | FastAPI + uvicorn                                              |
| Bot             | python-telegram-bot (proceso separado, comunica por HTTP)      |
| Embeddings      | `intfloat/multilingual-e5-small` (prefijos "passage:" / "query:") |
| Vector store    | ChromaDB PersistentClient                                      |
| BM25            | rank-bm25 o bm25s (en memoria, por idioma)                     |
| Fusión          | Reciprocal Rank Fusion (k=60)                                  |
| Lang detection  | lingua-py (solo ES+EN cargados)                                |
| Config          | pydantic-settings (`GEIST_API_*`, `GEIST_BOT_*`)               |
| Logging         | structlog (JSON estructurado)                                  |
| Errores         | Sentry SDK                                                     |
| Monorepo        | uv workspaces (Python 3.11+)                                   |
| Linting/formato | ruff                                                           |
| Tipos           | mypy --strict                                                  |
| Task runner     | just                                                           |
| Contenedores    | docker-compose (dev)                                           |

Referencias completas en [docs/base-standards.md](../docs/base-standards.md).

## Estructura del monorepo

```
services/api/       FastAPI — /v1/search, /v1/feedback, /v1/health, /v1/metrics
services/bot/       Bot Telegram (@geistBot)
shared/             geist_shared — modelos Pydantic compartidos
ingestion/          Pipeline PDF → Markdown → chunks JSONL
eval/               Golden dataset + métricas (Recall@5, MRR, faithfulness)
tests/              Tests de integración y E2E
docs/               base-standards.md, adr/, ...
.claude/            Contexto Claude Code (agents, commands, us/)
openspec/           Artefactos OpenSpec (changes/, specs/)
```

## Disciplina de rama (OBLIGATORIO)

Antes de tocar código para una tarea:

1. `git branch --show-current`
2. Si estás en `main`, crear la rama **antes** de cualquier edit:
   - `feature/TAR-XX-<short>` para tareas numeradas del plan
   - `chore/<short>` para tooling, config, refactor sin ticket
   - `fix/<short>` para bugs sin ticket
3. Nunca commitear código de implementación directamente a `main`

## Flujo de trabajo con tareas (TAR-XX)

- Las tareas viven en `.claude/us/TAR-XX <Título>.md`
- `/enrich-us TAR-XX` lee el fichero, añade/refresca `## Enhanced`
- `/opsx:propose` scaffoldea artefactos en `openspec/changes/<name>/`
- `/opsx:apply` implementa siguiendo `tasks.md`
- `/opsx:archive` mueve a `openspec/changes/archive/YYYY-MM-DD-<name>/`

## Estado actual del desarrollo

| Fase | Descripción             | Estado      |
|------|-------------------------|-------------|
| F0   | Bootstrap monorepo      | ✅ Completo  |
| F1   | Ingesta PDF → chunks    | 🔄 En curso  |
| F2   | Núcleo RAG (ChromaDB)   | ⏳ Pendiente |
| F3   | Bot Telegram            | ⏳ Pendiente |
| F5   | Deploy (Railway/Fly.io) | ⏳ Pendiente |
| F6+  | Post-MVP                | ❌ Diferido  |

## ADRs activos

| ADR     | Decisión                                          |
|---------|---------------------------------------------------|
| ADR-001 | MVP sin capa LLM — retrieval literal con citas    |
| ADR-002 | pymupdf4llm (AGPL-3.0) — repo debe ser público   |

## Principios técnicos

- **API-first**: contratos estables antes de UI
- **SOLID, DRY, KISS**: sin sobre-ingeniería
- **mypy --strict** en todo el código fuente
- **No LLM en MVP** — placeholder `llm_answer: str | None = None` en SearchResponse
- **Thresholds provisionales** hasta calibración con golden dataset (TAR-03d)
- **User IDs como SHA-256+salt**, nunca raw
- **Repo público** (condición ADR-002)
