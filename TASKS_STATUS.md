# Geist — Estado de Implementación

**Última actualización:** 2026-07-02 (post TAR-02 completado)

---

## Resumen de Progreso

| Fase | Descripción | Progreso | Estado |
|------|-------------|----------|--------|
| **F0** | Bootstrap monorepo | 100% | ✅ Completado |
| **F1** | Ingesta PDF → chunks | 100% | ✅ Completado |
| **F2** | Núcleo RAG (ChromaDB) | 12% | 🔄 En curso |
| **F3** | Bot Telegram | 0% | ⏳ Pendiente |
| **F5** | Deploy (Railway/Fly.io) | 0% | ⏳ Pendiente |
| **F6+** | Post-MVP | 0% | ❌ Diferido |

**Progreso global:** 2.12/5 fases core completadas (42%)

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

### 🔄 F2 — Núcleo RAG (EN CURSO - 12%)

#### TAR-02 — Indexación embeddings multilingüe
- **Estado:** ✅ Completado (2026-07-02)
- **Prioridad:** 5 (crítica)
- **Estimación:** 6–8 h
- **Completado:** 2026-07-02
- **Archivado:** openspec/changes/archive/2026-07-02-tar-02-indexing-embeddings/
- **Entregables:**
  - [x] E5MultilingualSmall wrapper con prefijos "passage:" / "query:"
  - [x] ChromaDB PersistentClient en `services/api/src/geist_api/indexing/`
  - [x] IndexManager con indexación incremental por content_hash
  - [x] CLI: `python -m geist_api.cli.index` (alias: `just index`)
  - [x] Tests unitarios + integración + smoke tests bilingües
  - [x] Documentación en README.md y base-standards.md
  - [x] Specs creadas: e5-embedding-wrapper, incremental-indexing, vector-indexing

**Datos listos para indexar:**
```
data/chunks/{es,en}/{core,faq,its,reinforcements}/chunks.jsonl
Total: 937+ chunks listos para indexar con `just index`
```

#### TAR-02b — Language detection (lingua-py)
- **Estado:** ⏳ Pendiente
- **Prioridad:** 5 (crítica - bloqueante para TAR-03)
- **Estimación:** 2–3 h
- **Dependencias:** TAR-00 ✅
- **Bloqueadores:** Ninguno
- **Tareas previstas:**
  - [ ] Instalar lingua-language-detector (solo ES+EN, no los 75 idiomas)
  - [ ] Implementar `detect_language(text: str) -> tuple[Lang, float]` en `services/api/src/geist_api/core/language.py`
  - [ ] Política: confianza ≥0.7 → detectado; <0.7 → fallback ES
  - [ ] Override explícito: parámetro `?lang=en` en API, comandos `/en` `/es` en bot
  - [ ] Tests: 100 ejemplos balanceados, >95% precisión en queries >3 palabras, latencia <5 ms

#### TAR-03 — Retrieval híbrido con filtro por idioma
- **Estado:** ⏳ Pendiente
- **Prioridad:** 5 (crítica)
- **Estimación:** 8–10 h
- **Dependencias:** TAR-02 ✅, TAR-02b ⏳
- **Bloqueadores:** TAR-02b debe completarse primero
- **Tareas previstas:**
  - [ ] Implementar BM25 en memoria (rank-bm25 o bm25s), índice separado por idioma
  - [ ] Implementar `hybrid_retrieve(query, lang, top_k)`: vector search ChromaDB + BM25 paralelo
  - [ ] Fusión por Reciprocal Rank Fusion (RRF, k=60)
  - [ ] Score gating: mapear score fusionado a "high"/"low"/"none" (thresholds provisionales: 0.80/0.65)
  - [ ] Fallback cross-lang: si lang-query no da hit ≥LOW pero otro idioma da ≥HIGH → retornar con disclaimer
  - [ ] Definir y retornar RetrievalResult: hits, lang_detected, lang_searched, confidence_level, cross_lang_fallback, elapsed_ms
  - [ ] Test: p95 latencia <300 ms local, recall@5 >85% con primeras 10 queries del golden set

#### TAR-03d — Golden dataset + métricas eval
- **Estado:** ⏳ Pendiente
- **Prioridad:** 5 (crítica - calibra thresholds)
- **Estimación:** 8–10 h
- **Dependencias:** TAR-03 ⏳
- **Tareas previstas:**
  - [ ] Recopilar 30 queries ES + 30 EN de reglas reales + ≥10 queries negativas
  - [ ] Formato eval/golden_set.jsonl con expected_canonical_rules, pages, must_mention, expected_behavior
  - [ ] Implementar script geist-eval: Recall@5, MRR, faithfulness rate, citation accuracy
  - [ ] Calibrar HIGH_CONFIDENCE y LOW_CONFIDENCE basado en distribución de scores reales
  - [ ] Configurar CI: geist-eval con LLM mockeado, degradación >5% bloquea merge

#### TAR-03b — Capa LLM condicional + prompt restrictivo
- **Estado:** ⏳ Pendiente (diferido a post-MVP por ADR-001)
- **Prioridad:** 2 (baja - no bloqueante para MVP)
- **Estimación:** 6–8 h
- **Dependencias:** TAR-03 ⏳

#### TAR-03c — Faithfulness validator (anti-alucinación)
- **Estado:** ⏳ Pendiente (diferido a post-MVP por ADR-001)
- **Prioridad:** 2 (baja - solo relevante con LLM)
- **Estimación:** 4–6 h
- **Dependencias:** TAR-03b ⏳

#### TAR-05 — Seguridad: rate limit + validación input
- **Estado:** ⏳ Pendiente
- **Prioridad:** 4 (alta)
- **Estimación:** 5–7 h
- **Dependencias:** TAR-03 ⏳
- **Tareas previstas:**
  - [ ] Autenticación bot↔API con shared secret X-Internal-Auth
  - [ ] slowapi: rate limiting por chat_id/IP
  - [ ] Validación input: max 500 chars, rechazo control chars (excepto \n \t)
  - [ ] NO filtrar <>{} — válidos en queries wargaming

#### TAR-05b — Cache de respuestas
- **Estado:** ⏳ Pendiente (post-MVP)
- **Prioridad:** 3 (media)
- **Estimación:** 3–4 h

#### TAR-09 — Tests + CI pipeline
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

#### TAR-04 — Bot Telegram @geistBot (proceso separado)
- **Estado:** ⏳ Pendiente
- **Prioridad:** 5 (crítica para interfaz usuario)
- **Estimación:** 8–12 h
- **Dependencias:** TAR-03 ⏳, TAR-05 ⏳
- **Tareas previstas:**
  - [ ] Configurar python-telegram-bot en `services/bot/`
  - [ ] Handler para /start, /help, /search
  - [ ] HTTP client → API (`services/bot/src/geist_bot/client.py`)
  - [ ] Formateo de respuestas (high/low/none confidence)
  - [ ] Rate limiting por usuario
  - [ ] Logging estructurado con structlog

---

### ⏳ F5 — Deploy (PENDIENTE)

#### TAR-08 — Despliegue API + Bot independientes
- **Estado:** ⏳ Pendiente
- **Prioridad:** 4 (alta)
- **Estimación:** 8–12 h
- **Dependencias:** TAR-04 ⏳
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
- ✅ **Completadas:** 4 (TAR-00, TAR-01, TAR-01b, TAR-02)
- 🔄 **En curso:** 0
- ⏳ **Pendientes críticas:** 5 (TAR-02b, TAR-03, TAR-03d, TAR-04, TAR-08)
- ⏳ **Pendientes no bloqueantes:** 4+ (TAR-05, TAR-05b, TAR-09, TAR-11, TAR-13)
- ❌ **Diferidas post-MVP:** 3+ (TAR-03b, TAR-03c, LLM layer)

### Estimaciones
- **Tiempo invertido:** ~24–32 h (F0 + F1 + TAR-02)
- **Tiempo estimado restante MVP:** ~35–50 h (TAR-02b → TAR-08)
- **Total proyecto MVP:** ~59–82 h

### Hitos Críticos
- [x] **M1:** Monorepo funcional (F0) — ✅ Completado
- [x] **M2:** Pipeline de ingesta E2E (F1) — ✅ Completado
- [ ] **M3:** API /v1/search funcional (F2) — ⏳ En espera
- [ ] **M4:** Bot Telegram funcional (F3) — ⏳ En espera
- [ ] **M5:** Deploy en producción (F5) — ⏳ En espera

---

## Bloqueadores Actuales

**TAR-03 bloqueado por TAR-02b:** El retrieval híbrido necesita language detection para funcionar correctamente.

---

## Próximos Pasos Inmediatos (Crítico Path)

1. **TAR-02b** — Language detection con lingua-py (2–3 h) ⚡ **DESBLOQUEA TODO**
2. **TAR-03** — Retrieval híbrido Vector+BM25+RRF (8–10 h)
3. **TAR-03d** — Golden dataset para calibrar thresholds (8–10 h)
4. **TAR-04** — Bot Telegram @geistBot (8–12 h)
5. **TAR-08** — Deploy a Railway/Fly.io (8–12 h)

**Demo técnica funcional:** Después de TAR-03 (~10–13 h desde ahora)  
**Bot funcional en Telegram:** Después de TAR-04 (~18–25 h desde ahora)

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
