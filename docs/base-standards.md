# Geist — Base Standards

Single source of truth for the Geist project. Read this before starting any task.

## Product

RAG system for querying Infinity N5 tabletop wargame rules. Bilingual ES/EN. API-first. Telegram bot (@geistBot). Non-monetized, open-source (required by ADR-002).

**North star:** Literal accuracy over fluent prose. Return exact rule fragments with page citations.

---

## Stack

| Layer           | Technology                                         | Notes                                      |
|-----------------|----------------------------------------------------|--------------------------------------------|
| API             | FastAPI 0.111+ + uvicorn                           | Async, OpenAPI hidden in production        |
| Bot             | python-telegram-bot 21+                            | Separate process, communicates via HTTP    |
| Embeddings      | `intfloat/multilingual-e5-small`                   | **Mandatory prefixes** (see below)         |
| Vector store    | ChromaDB PersistentClient                          | Single collection, lang filtered at query  |
| BM25            | rank-bm25 or bm25s                                 | In-memory, separate index per language     |
| Fusion          | Reciprocal Rank Fusion (RRF, k=60)                 |                                            |
| Lang detection  | lingua-py                                          | Load ES+EN only (not all 75 languages)     |
| Config          | pydantic-settings                                  | `GEIST_API_*` / `GEIST_BOT_*` prefixes    |
| Logging         | structlog (structured JSON)                        | Never use `print()` or stdlib `logging`    |
| Errors          | Sentry SDK (unhandled exceptions only, ignore 4xx) |                                            |
| Monorepo        | uv workspaces                                      | Python 3.11+                               |
| Linting         | ruff (lint + format)                               |                                            |
| Types           | mypy --strict                                      | No `Any` in own code                       |
| Task runner     | just                                               |                                            |
| Containers      | docker-compose (dev only)                          |                                            |

---

## Monorepo Structure

```
services/
  api/            FastAPI service
    src/geist_api/
      main.py     App factory + health/metrics endpoints
      settings.py pydantic-settings (GEIST_API_*)
      routers/    One file per feature (search.py, feedback.py...)
      core/       Business logic (retrieval, language, cache...)
  bot/            Telegram bot
    src/geist_bot/
      main.py     Application + command handlers
      settings.py pydantic-settings (GEIST_BOT_*)
      client.py   HTTP client → API
shared/
  geist_shared/
    models.py     SearchRequest/Response, Chunk, Feedback, Health
    chunk_models.py  Chunk Pydantic model
ingestion/
  src/geist_ingestion/
    extract.py    PDF → Markdown (pymupdf4llm)
    chunk.py      Markdown → JSONL chunks
    validate.py   ES↔EN alignment
    __main__.py   CLI entry point
eval/
  src/geist_eval/
    runner.py     Recall@5, MRR, faithfulness rate
    golden_set.jsonl  60+ queries (30 ES + 30 EN + ≥10 negatives)
tests/            Integration and E2E tests
docs/
  base-standards.md  ← this file
  adr/               Architecture Decision Records
data/              gitignored — raw PDFs, processed Markdown, ChromaDB
```

---

## API Contract

### Endpoints

| Method | Path            | Auth                   | Description              |
|--------|-----------------|------------------------|--------------------------|
| POST   | /v1/search      | X-Internal-Auth (bot)  | Hybrid retrieval         |
| POST   | /v1/feedback    | X-Internal-Auth        | Thumbs up/down           |
| GET    | /v1/health      | None                   | Health check             |
| GET    | /v1/metrics     | None (Prometheus)      | Metrics endpoint         |

### Key response fields (SearchResponse)
- `confidence_level`: `"high"` / `"low"` / `"none"` (thresholds provisional until TAR-03d)
- `cross_lang_fallback`: `true` when searched other language
- `llm_answer: str | None`: always `None` in MVP (placeholder for F9)

---

## Critical Rules

### Embeddings (non-negotiable)
```python
# ALWAYS add prefix when indexing
text_to_index = f"passage: {chunk.content}"

# ALWAYS add prefix when querying
query_vector = model.encode(f"query: {user_query}")
```
Missing these prefixes causes 20–30% quality degradation. No exceptions.

### Language detection
```python
# confidence ≥ 0.7 → detected language
# confidence < 0.7 → fallback to ES
# Override: ?lang=en in API, /en /es commands in bot
```

### Confidence thresholds (PROVISIONAL)
```python
HIGH_CONFIDENCE = 0.80  # PROVISIONAL — calibrate with TAR-03d golden set
LOW_CONFIDENCE  = 0.65  # PROVISIONAL — calibrate with TAR-03d golden set
```
Always mark these as provisional in code comments. Do not treat them as calibrated values.

### Privacy
```python
# User IDs must be hashed BEFORE any storage
import hashlib
hashed_id = hashlib.sha256(f"{salt}{telegram_user_id}".encode()).hexdigest()
# NEVER store raw telegram_user_id
```

### Input validation
- Max 500 characters
- Reject non-printable control characters (except `\n` and `\t`)
- Do NOT filter `<>{}` — valid in wargaming queries

### ChromaDB Persistence (CRITICAL)

ChromaDB requires persistent volume mount in production:
- **Environment variable**: `GEIST_API_CHROMA_PATH` (default: `data/chroma`)
- **Deployment**: Mount persistent volume at this path in Railway/Fly.io
- **Without volume**: Index is lost on every deploy (CRITICAL BLOCKER)
- **Health check**: Verify collection contains >0 chunks after indexing
- **Backup**: Original chunks JSONL is source of truth for rebuilds

Example Railway/Fly.io volume config:
```toml
[mounts]
  source = "chroma_data"
  destination = "/app/data/chroma"
```

---

## Code Quality

### Python style
- **Type hints everywhere** — mypy --strict must pass
- **No `Any`** in own code — use concrete types or proper generics
- **Pydantic v2 syntax** — `@field_validator`, `model_dump()`, not v1 patterns
- **`from __future__ import annotations`** at top of every module
- **structlog** for all logging — bind context early, emit late
- **Single responsibility** — small functions, one reason to change

### Test pyramid
- **Unit tests**: chunking, normalisation, language detection, faithfulness validator (no network)
- **Integration tests**: E2E pipeline with reduced fixture manual
- **API tests**: httpx.AsyncClient against FastAPI in-process, LLM mocked
- **Coverage targets**: >85% in `validation/` and `retrieval/`, >70% global

### Running quality checks
```bash
just lint        # ruff check + format --check
just typecheck   # mypy --strict
just test        # pytest
just check       # all three
```

---

## Git Workflow

### Branch naming
- `feature/TAR-XX-short-description` — numbered tasks from the plan
- `chore/short-description` — tooling, config, refactor (no ticket)
- `fix/short-description` — bugs without ticket

### Commit format (Conventional Commits)
```
feat(TAR-02): implement ChromaDB indexing with multilingual-e5-small
fix(TAR-03): apply passage: prefix when indexing chunks
chore: upgrade ruff to 0.5
docs(TAR-01): add ADR-002 for pymupdf4llm license
test(TAR-03d): add 30 ES golden queries for threshold calibration
```

Types: `feat`, `fix`, `refactor`, `chore`, `docs`, `test`
TAR-XX required for `feat` and `fix`; optional for others.
Commit messages in **English**.

### Never commit to main
Create the branch FIRST. No exceptions.

---

## Architecture Decisions (Active ADRs)

| ADR     | Decision                                                       | Status   |
|---------|----------------------------------------------------------------|----------|
| ADR-001 | MVP without LLM layer — literal retrieval with page citations  | Active   |
| ADR-002 | Use pymupdf4llm (AGPL-3.0) — repo must remain public          | Active   |

Full ADR texts in `docs/adr/`.

### ADR-001 implications
- `llm_answer` field exists in `SearchResponse` but is always `None` in MVP
- Endpoint is `/v1/search` (not `/v1/ask`) — reflects actual behavior
- LLM integration deferred to F9, pending metrics from TAR-03d

### ADR-002 implications
- Repository **must be public** while pymupdf4llm is a dependency
- If monetisation is ever considered: migrate to `docling` (MIT) or buy Artifex commercial license

---

## Development Phases (MVP)

| Phase | Description              | Key tasks              | Status      |
|-------|--------------------------|------------------------|-------------|
| F0    | Monorepo bootstrap       | TAR-00                 | ✅ Complete  |
| F1    | PDF ingestion            | TAR-01, TAR-01b        | 🔄 In progress |
| F2    | RAG core                 | TAR-02 through TAR-09  | ⏳ Pending  |
| F3    | Telegram bot             | TAR-04                 | ⏳ Pending  |
| F5    | Deploy                   | TAR-08                 | ⏳ Pending  |

Do not start F2 work until F1 produces validated chunks from the real PDFs.
