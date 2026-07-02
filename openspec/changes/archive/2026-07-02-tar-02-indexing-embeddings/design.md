## Context

TAR-01b produces chunked JSONL files with rich metadata (`canonical_rule_id`, `lang`, `manual_id`, `section_path`, `page_start`, `page_end`, `content_hash`). These chunks need to be indexed in a vector store to enable semantic retrieval for the RAG pipeline.

Current state: No indexing exists yet. This is the first component of F2 (RAG core).

Constraints:
- Must support bilingual ES/EN with language-specific filtering at query time
- Must preserve chunk metadata for citation generation
- Deployment requires persistent storage (Railway/Fly.io volumes)
- No GPU available in deployment environment (CPU-only inference)

## Goals / Non-Goals

**Goals:**
- Index chunks with multilingual embeddings that work equally well for ES and EN
- Enable incremental re-indexing (only process new/changed chunks)
- Provide clean separation between embedding model wrapper and indexing logic
- CLI tool for manual/scripted indexing operations
- Foundation for retrieval module (TAR-03)

**Non-Goals:**
- Query-time retrieval (handled by TAR-03)
- BM25 indexing (handled by TAR-03)
- Automatic reindexing on chunk file changes (manual CLI invocation only in MVP)
- GPU acceleration or quantization optimizations (defer to post-MVP if needed)

## Decisions

### 1. Vector Store: ChromaDB with PersistentClient

**Decision:** Use ChromaDB with `PersistentClient` (not Ephemeral or HTTP client).

**Alternatives considered:**
- **Qdrant**: More production-ready but adds deployment complexity (separate service). Overkill for MVP scale (<10k chunks).
- **FAISS with pickle persistence**: Fast but requires manual metadata management. ChromaDB gives us metadata filtering built-in.
- **Weaviate**: Feature-rich but heavy. Needs separate deployment.

**Rationale:** ChromaDB PersistentClient gives us:
- Single-process deployment (no separate vector DB service)
- Built-in metadata filtering (`where={"lang": "es"}`)
- Incremental updates without full rebuilds
- Cosine similarity with HNSW index out of the box

**Trade-off:** ChromaDB is less battle-tested at scale than Qdrant/Weaviate, but our scale (<10k chunks, <50 req/min) is well within its capabilities.

### 2. Embedding Model: intfloat/multilingual-e5-small

**Decision:** Use `intfloat/multilingual-e5-small` (118M params) with mandatory `"passage:"` and `"query:"` prefixes.

**Alternatives considered:**
- **sentence-transformers/paraphrase-multilingual-mpnet-base-v2**: Good multilingual support but no instruction tuning. E5 specifically trained for passage/query asymmetry.
- **OpenAI text-embedding-3-small**: Better quality but adds API cost + latency. Eliminates self-hosted deployment.
- **intfloat/multilingual-e5-large** (560M params): 5% better quality but 4× slower and doesn't fit comfortably on Railway's free tier CPU.

**Rationale:** E5-small hits the sweet spot:
- Trained specifically for retrieval with passage/query prefixes
- Fast CPU inference (<100ms for batch of 100 chunks)
- Small enough for Railway/Fly.io deployment (<500 MB model download)
- Explicitly multilingual (trained on 100+ languages including ES/EN)

**Critical requirement:** Prefixes are **non-negotiable**. Without them, quality drops 20-30% (documented in E5 paper). Wrapper API enforces this.

### 3. Module Structure: Separation of Concerns

**Decision:** Split into 3 modules:
- `embedder.py`: Model wrapper, enforces prefixes, protocol-based interface
- `chroma_client.py`: ChromaDB singleton, collection management
- `indexer.py`: Business logic (load chunks, dedupe, batch, index)

**Rationale:**
- Embedder is testable in isolation (mock ChromaDB not needed)
- ChromaDB client can be reused by retrieval module (TAR-03)
- IndexManager contains all indexing logic, easily extended for stats/monitoring

### 4. Incremental Indexing Strategy: content_hash-based

**Decision:** Query existing chunks' `content_hash` metadata from ChromaDB, filter out duplicates before embedding.

**Alternatives considered:**
- **Separate SQLite manifest**: Faster lookup but adds another persistence layer. ChromaDB metadata query is fast enough (<1s for 10k chunks).
- **Timestamp-based**: Fragile (doesn't detect changed content). Hash is deterministic.

**Rationale:** ChromaDB stores metadata natively. Querying `content_hash` is a single call. No additional dependencies.

**Trade-off:** If corpus grows to 100k+ chunks, manifest approach might be faster. Defer optimization until measured.

### 5. CLI Design: Simple Entry Point

**Decision:** CLI script `geist-index <chunks.jsonl> [--full]` as Python entry point.

- Default: incremental (skip existing hashes)
- `--full`: Force full reindex (ignores existing hashes)

**Rationale:** Matches `just` command style. Easy to script in CI or manual ops. No complex flags needed in MVP.

## Risks / Trade-offs

### 1. E5 Prefixes Forgotten → Silent Quality Degradation

**Risk:** Developers use embedding model directly without wrapper, forgetting prefixes.

**Mitigation:**
- Wrapper class with explicit `encode_passages()` / `encode_query()` methods (no generic `encode()`)
- Test that verifies non-prefixed encoding produces different vectors (cosine similarity <0.9)
- Documentation comment with **OBLIGATORIO** / **MANDATORY** warnings

### 2. ChromaDB Persistent Path Not Mounted → Index Lost on Redeploy

**Risk:** If `GEIST_API_CHROMA_PATH` points to ephemeral container filesystem, index is lost on every deploy. Silent failure mode.

**Mitigation:**
- Document volume requirement in deployment guide (TAR-08 dependency)
- Add health check endpoint that verifies ChromaDB contains >0 chunks
- Log WARNING on startup if collection is empty after first indexing run

### 3. Incremental Indexing Hash Collision

**Risk:** Two different chunks produce same `content_hash` (SHA-256 collision), causing one to be skipped.

**Mitigation:** SHA-256 collision probability is ~10^-60. For corpus size <1 million chunks, risk is negligible. If corpus grows to billions of chunks, reconsider strategy.

### 4. Model Download on First Run (~450 MB)

**Risk:** First run downloads model from HuggingFace, adding ~2-5 min cold start. Network failure = hard crash.

**Mitigation:**
- Pre-download model in Docker image build (ADD to `~/.cache/huggingfance/`)
- Offline mode for deployments (set `TRANSFORMERS_OFFLINE=1` after first successful download)
- Document expected download in README

### 5. CPU Inference Latency

**Risk:** Indexing 10k chunks at ~100ms per batch of 100 = ~10 minutes. Acceptable for MVP but might be bottleneck at scale.

**Mitigation:** Defer GPU optimization until measured. If needed post-MVP:
- Add CUDA support via `device="cuda"` flag in SentenceTransformer init
- Investigate ONNX quantization for 2-3× CPU speedup

## Migration Plan

N/A — This is the initial implementation. No existing index to migrate.

**Deployment steps:**
1. Add `chromadb` and `sentence-transformers` dependencies via `uv sync`
2. Configure `GEIST_API_CHROMA_PATH` environment variable (default: `data/chroma`)
3. Mount persistent volume at `GEIST_API_CHROMA_PATH` in Railway/Fly.io
4. Run `geist-index data/processed/chunks_all.jsonl` to perform initial indexing
5. Verify smoke test: query returns chunks with correct language filtering

**Rollback:** Delete ChromaDB directory and restart from backup chunks JSONL. No schema migrations needed.

## Open Questions

None — design is ready for implementation.
