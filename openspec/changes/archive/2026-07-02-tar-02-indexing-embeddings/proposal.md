## Why

TAR-01b produces chunked JSONL files from PDF manuals but they're not searchable yet. We need vector embeddings to enable semantic search across bilingual (ES/EN) Infinity N5 rules. Without indexation, the RAG pipeline cannot retrieve relevant chunks for user queries.

## What Changes

- Add ChromaDB as persistent vector store with `intfloat/multilingual-e5-small` embeddings
- Create indexing module in `services/api/src/geist_api/indexing/` with embedder, indexer, and ChromaDB client
- Add CLI command `geist-index` to process JSONL chunks into ChromaDB with language metadata
- Implement incremental indexing (skip chunks already indexed by content hash)
- Add smoke tests verifying bilingual separation (ES/EN queries don't contaminate each other)
- Add settings configuration for ChromaDB persistence path

## Capabilities

### New Capabilities

- `vector-indexing`: Index chunks from JSONL into ChromaDB with multilingual embeddings and structured metadata (lang, manual_id, canonical_rule_id, pages, section_path)
- `incremental-indexing`: Skip re-indexing chunks already present based on content hash, enabling fast delta updates
- `e5-embedding-wrapper`: Enforce mandatory "passage:" and "query:" prefixes for E5 model to prevent 20-30% quality degradation

### Modified Capabilities

<!-- No existing capabilities are being modified at the spec level -->

## Impact

**New Code:**
- `services/api/src/geist_api/indexing/embedder.py` — E5MultilingualSmall wrapper
- `services/api/src/geist_api/indexing/indexer.py` — IndexManager with batch processing
- `services/api/src/geist_api/indexing/chroma_client.py` — ChromaDB singleton
- `services/api/src/geist_api/cli/index.py` — CLI entry point
- `services/api/src/geist_api/settings.py` — Add `GEIST_API_CHROMA_PATH` setting
- `tests/integration/test_indexing_smoke.py` — Bilingual separation tests

**Dependencies:**
- Add `chromadb ^0.5.0` and `sentence-transformers ^3.0.0` to `services/api/pyproject.toml`
- Downloads `intfloat/multilingual-e5-small` model (118M params, ~450 MB) to HuggingFace cache on first run

**Deployment:**
- ChromaDB requires persistent volume mount at `GEIST_API_CHROMA_PATH` (default: `data/chroma`) to survive deployments
- Without volume persistence, index must be rebuilt on every deploy (critical blocker)

**Performance:**
- Full indexing: <10 min on modern CPU (no GPU required)
- Disk usage: <400 MB for complete MVP corpus
- RAM peak: <2 GB during indexing
