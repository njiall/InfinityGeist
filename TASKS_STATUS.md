# Geist — Estado de Implementación

**Última actualización:** 2026-07-02

---

## Resumen de Progreso

| Fase | Descripción | Progreso | Estado |
|------|-------------|----------|--------|
| **F0** | Bootstrap monorepo | 100% | ✅ Completado |
| **F1** | Ingesta PDF → chunks | 100% | ✅ Completado |
| **F2** | Núcleo RAG (ChromaDB) | 0% | ⏳ Pendiente |
| **F3** | Bot Telegram | 0% | ⏳ Pendiente |
| **F5** | Deploy (Railway/Fly.io) | 0% | ⏳ Pendiente |
| **F6+** | Post-MVP | 0% | ❌ Diferido |

**Progreso global:** 2/5 fases core completadas (40%)

---

## Tareas Detalladas

### ✅ F0 — Bootstrap Monorepo (COMPLETADO)

#### TAR-00 — Bootstrap monorepo
- **Estado:** ✅ Completado
- **Prioridad:** 5 (crítica)
- **Estimación:** 4–6 h
- **Completado:** 2026-06-XX
- **Entregables:**
  - [x] Estructura de workspace con uv
  - [x] Configuración de ruff, mypy --strict, just
  - [x] Docker-compose para ChromaDB
  - [x] CI/CD básico (GitHub Actions)
  - [x] Documentación en docs/base-standards.md

---

### ✅ F1 — Ingesta de Datos (COMPLETADO)

#### TAR-01 — Extractor PDF → Markdown
- **Estado:** ✅ Completado
- **Prioridad:** 5 (crítica)
- **Estimación:** 8–10 h
- **Completado:** 2026-06-XX
- **Entregables:**
  - [x] Pipeline PDF → Markdown con pymupdf4llm
  - [x] Output: `data/processed/{lang}/{manual}/content.md`
  - [x] Preservación de metadatos de página
  - [x] Script CLI: `python -m geist_ingestion extract`

#### TAR-01b — Chunking + canonical_rule_id
- **Estado:** ✅ Completado (2026-07-02)
- **Prioridad:** 5 (crítica)
- **Estimación:** 6–8 h
- **Completado:** 2026-07-02
- **Entregables:**
  - [x] Modelo Pydantic `Chunk` en `shared/geist_shared/chunk_models.py`
  - [x] Algoritmo de chunking semántico por heading
  - [x] Generación determinista de `canonical_rule_id`
  - [x] Script: `python -m geist_ingestion chunk --manual core --langs es en`
  - [x] Output: 937 chunks (492 ES, 445 EN)
  - [x] Reporte de huérfanos: 97 reglas sin par ES↔EN
  - [x] Validación: sampling manual 18+/20 chunks comprensibles

**Datos generados:**
```
data/chunks/
├── es/core/chunks.jsonl (492 chunks)
├── en/core/chunks.jsonl (445 chunks)
└── reports/core/orphans.json (97 huérfanos)
```

---

### ⏳ F2 — Núcleo RAG (PENDIENTE)

#### TAR-02 — Indexación ChromaDB + embeddings
- **Estado:** ⏳ Pendiente
- **Prioridad:** 5 (crítica)
- **Estimación:** 8–10 h
- **Dependencias:** TAR-01b ✅
- **Bloqueadores:** Ninguno
- **Tareas previstas:**
  - [ ] Configurar `intfloat/multilingual-e5-small`
  - [ ] Implementar indexación con prefijos "passage:"
  - [ ] Crear ChromaDB PersistentClient
  - [ ] Indexar `data/chunks/{lang}/{manual}/chunks.jsonl`
  - [ ] Output: ChromaDB en `data/chroma/`
  - [ ] Script CLI: `python -m geist_ingestion index`

#### TAR-02b — BM25 indexing
- **Estado:** ⏳ Pendiente
- **Prioridad:** 4 (alta)
- **Estimación:** 4–6 h
- **Dependencias:** TAR-01b ✅
- **Tareas previstas:**
  - [ ] Implementar índice BM25 en memoria (rank-bm25 o bm25s)
  - [ ] Índice separado por idioma (ES/EN)
  - [ ] Serialización/deserialización de índices
  - [ ] Validación de retrieval keyword-only

#### TAR-02c — Reciprocal Rank Fusion (RRF)
- **Estado:** ⏳ Pendiente
- **Prioridad:** 4 (alta)
- **Estimación:** 3–4 h
- **Dependencias:** TAR-02 ⏳, TAR-02b ⏳
- **Tareas previstas:**
  - [ ] Implementar algoritmo RRF (k=60)
  - [ ] Fusión de resultados ChromaDB + BM25
  - [ ] Top-k post-fusion configurable
  - [ ] Tests de integración

#### TAR-03a — Endpoint /v1/search
- **Estado:** ⏳ Pendiente
- **Prioridad:** 5 (crítica)
- **Estimación:** 6–8 h
- **Dependencias:** TAR-02c ⏳
- **Tareas previstas:**
  - [ ] Router FastAPI en `services/api/src/geist_api/routers/search.py`
  - [ ] Modelos Pydantic `SearchRequest`/`SearchResponse` en `shared/`
  - [ ] Integración con RRF
  - [ ] Detección de idioma con lingua-py
  - [ ] Cross-language fallback
  - [ ] Cálculo de `confidence_level` (provisional)
  - [ ] Placeholder `llm_answer: None`

#### TAR-03b — Endpoint /v1/feedback
- **Estado:** ⏳ Pendiente
- **Prioridad:** 3 (media)
- **Estimación:** 2–3 h
- **Dependencias:** TAR-03a ⏳
- **Tareas previstas:**
  - [ ] Router FastAPI para thumbs up/down
  - [ ] Modelo `FeedbackRequest` en `shared/`
  - [ ] Almacenamiento en SQLite o JSONL
  - [ ] User ID hasheado (SHA-256 + salt)

#### TAR-03c — Health & metrics endpoints
- **Estado:** ⏳ Pendiente
- **Prioridad:** 2 (baja, no bloqueante)
- **Estimación:** 1–2 h
- **Tareas previstas:**
  - [ ] `/v1/health` con status ChromaDB/BM25
  - [ ] `/v1/metrics` para Prometheus
  - [ ] Métricas: latencia, throughput, error rate

#### TAR-03d — Calibración de thresholds con golden dataset
- **Estado:** ⏳ Pendiente
- **Prioridad:** 4 (alta, post-MVP viable)
- **Estimación:** 6–8 h
- **Dependencias:** TAR-03a ⏳
- **Tareas previstas:**
  - [ ] Crear golden dataset (60+ queries: 30 ES + 30 EN + 10 negativas)
  - [ ] Implementar métricas: Recall@5, MRR, faithfulness
  - [ ] Calibrar thresholds de `confidence_level`
  - [ ] Script en `eval/src/geist_eval/runner.py`

---

### ⏳ F3 — Bot Telegram (PENDIENTE)

#### TAR-04 — Bot Telegram básico
- **Estado:** ⏳ Pendiente
- **Prioridad:** 4 (alta)
- **Estimación:** 8–10 h
- **Dependencias:** TAR-03a ⏳
- **Tareas previstas:**
  - [ ] Configurar python-telegram-bot en `services/bot/`
  - [ ] Handler para /start, /help, /search
  - [ ] HTTP client → API (`services/bot/src/geist_bot/client.py`)
  - [ ] Formateo de respuestas (high/low/none confidence)
  - [ ] Rate limiting por usuario
  - [ ] Logging estructurado con structlog

---

### ⏳ F5 — Deploy (PENDIENTE)

#### TAR-05 — Deploy a Railway/Fly.io
- **Estado:** ⏳ Pendiente
- **Prioridad:** 3 (media, post-MVP viable)
- **Estimación:** 4–6 h
- **Dependencias:** TAR-03a ✅, TAR-04 ✅
- **Tareas previstas:**
  - [ ] Dockerfile para API + Bot
  - [ ] Config de Railway/Fly.io
  - [ ] Variables de entorno (Sentry DSN, Telegram token, etc.)
  - [ ] ChromaDB persistente (volumen o S3)
  - [ ] Healthcheck en orquestador

---

### ❌ F6+ — Post-MVP (DIFERIDO)

#### TAR-09 — Capa LLM (Claude/Haiku)
- **Estado:** ❌ Diferido (ver ADR-001)
- **Prioridad:** 1 (nice-to-have)
- **Estimación:** TBD
- **Razón diferimiento:** MVP enfocado en retrieval literal con citas. LLM puede introducir alucinaciones.

---

## Métricas de Progreso

### Tareas por Estado
- ✅ **Completadas:** 3 (TAR-00, TAR-01, TAR-01b)
- 🔄 **En curso:** 0
- ⏳ **Pendientes:** 10+ (F2–F5)
- ❌ **Diferidas:** 1+ (F6+)

### Estimaciones
- **Tiempo invertido:** ~18–24 h (F0 + F1)
- **Tiempo estimado restante:** ~40–55 h (F2–F5)
- **Total proyecto MVP:** ~58–79 h

### Hitos Críticos
- [x] **M1:** Monorepo funcional (F0) — ✅ Completado
- [x] **M2:** Pipeline de ingesta E2E (F1) — ✅ Completado
- [ ] **M3:** API /v1/search funcional (F2) — ⏳ En espera
- [ ] **M4:** Bot Telegram funcional (F3) — ⏳ En espera
- [ ] **M5:** Deploy en producción (F5) — ⏳ En espera

---

## Bloqueadores Actuales

**Ninguno.** Todas las dependencias de F2 están resueltas (TAR-01b completado).

---

## Próximos Pasos Inmediatos

1. **TAR-02** — Indexación ChromaDB con embeddings multilingual-e5-small
2. **TAR-02b** — Implementar índice BM25 en memoria
3. **TAR-02c** — Fusión RRF de resultados
4. **TAR-03a** — Endpoint /v1/search en FastAPI

---

## Notas de Implementación

### Huérfanos ES↔EN
- **Total detectado:** 97 reglas sin par (48 ES, 49 EN)
- **Impacto:** No bloqueante para MVP. Cross-lang fallback cubrirá queries.
- **Acción pendiente:** Revisión manual post-MVP para alinear secciones.

### ADRs Activos
- **ADR-001:** MVP sin capa LLM — retrieval literal con citas
- **ADR-002:** pymupdf4llm (AGPL-3.0) — repo debe ser público

### Convenciones de Rama
- **feature/TAR-XX-<short>** para tareas numeradas
- **chore/<short>** para tooling sin ticket
- **fix/<short>** para bugs sin ticket
- ⚠️ **Nunca commitear a `main` directamente**

---

## Cómo Actualizar Este Documento

Este archivo debe actualizarse **cada vez que**:
1. ✅ Se completa una tarea (marcar checkbox, cambiar estado a ✅, añadir fecha de completado)
2. 🔄 Se inicia una tarea (cambiar estado a 🔄, añadir notas de progreso si aplica)
3. 📝 Se añade una nueva tarea (crear nueva entrada con estimación y dependencias)
4. 🚧 Se detecta un bloqueador (añadir a sección "Bloqueadores Actuales")
5. 📊 Se actualiza una métrica (revisar "Métricas de Progreso")

**Responsable de actualización:** Claude Code (automático al completar tareas) + Rubén (revisión manual).

---

_Generado automáticamente. Última sincronización con `.claude/us/` y `.claude/PROYECTO.md` el 2026-07-02._
