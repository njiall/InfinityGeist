# Geist — Infinity N5 RAG Assistant

RAG system for querying Infinity N5 tabletop wargame rules. Bilingual ES/EN. API-first with Telegram bot (@geistBot).

**North star:** Literal accuracy over fluent prose. Return exact rule fragments with page citations.

---

## Quick Start

### Prerequisites

- Python 3.11+
- ~450 MB disk space for E5 embedding model (downloads on first run)

### Installation

```bash
# Install API package
cd services/api
pip install -e .

# Or with dev dependencies
pip install -e ".[dev]"
```

### Indexing Chunks

```bash
# Index chunks into ChromaDB
just index

# Or directly
python -m geist_api.cli.index data/processed/chunks_all.jsonl

# Force full reindex
python -m geist_api.cli.index data/processed/chunks_all.jsonl --full
```

**Note:** First run downloads `intfloat/multilingual-e5-small` model (~450 MB) from HuggingFace. This is cached locally and reused.

### Running Tests

```bash
just test           # Run all tests
just test-cov       # Run with coverage report
just check          # Run lint + typecheck + test
```

---

## Project Structure

See [docs/base-standards.md](docs/base-standards.md) for full documentation.

```
services/api/       FastAPI RAG service
  src/geist_api/
    indexing/       E5 embeddings + ChromaDB indexing
    cli/            CLI commands (geist-index)
shared/             Shared Pydantic models
ingestion/          PDF → Markdown → chunks pipeline
tests/              Unit + integration tests
docs/               Documentation and ADRs
```

---

## Key Technologies

- **Embeddings**: `intfloat/multilingual-e5-small` with mandatory "passage:" / "query:" prefixes
- **Vector store**: ChromaDB PersistentClient (requires volume mount in production)
- **API**: FastAPI + uvicorn
- **Bot**: python-telegram-bot (separate service)
- **Linting**: ruff, mypy --strict
- **Task runner**: just

---

## License

Open source (AGPL-3.0 due to pymupdf4llm dependency). Repository must remain public.

See [docs/adr/ADR-002-pdf-extractor-license.md](docs/adr/ADR-002-pdf-extractor-license.md) for details.
