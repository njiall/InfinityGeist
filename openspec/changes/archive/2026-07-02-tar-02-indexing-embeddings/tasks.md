## 1. Setup and Dependencies

- [x] 1.1 Add `chromadb = "^0.5.0"` to `services/api/pyproject.toml` dependencies
- [x] 1.2 Add `sentence-transformers = "^3.0.0"` to `services/api/pyproject.toml` dependencies
- [x] 1.3 Run `uv sync` to install new dependencies
- [x] 1.4 Add `GEIST_API_CHROMA_PATH` setting to `services/api/src/geist_api/settings.py` with default `"data/chroma"`
- [x] 1.5 Create `services/api/src/geist_api/indexing/` package with `__init__.py`

## 2. E5 Embedding Wrapper

- [x] 2.1 Create `services/api/src/geist_api/indexing/embedder.py` with `EmbeddingModel` protocol
- [x] 2.2 Implement `E5MultilingualSmall` class with `__init__` loading `intfloat/multilingual-e5-small`
- [x] 2.3 Implement `encode_passages(texts: list[str]) -> list[list[float]]` method with "passage: " prefix
- [x] 2.4 Implement `encode_query(text: str) -> list[float]` method with "query: " prefix
- [x] 2.5 Add docstrings marking prefix requirement as MANDATORY/OBLIGATORIO
- [x] 2.6 Create unit test `tests/unit/test_embedder.py` verifying prefixed vs non-prefixed embeddings differ (cosine < 0.9)
- [x] 2.7 Create unit test verifying query vs passage encoding differ for same text

## 3. ChromaDB Client

- [x] 3.1 Create `services/api/src/geist_api/indexing/chroma_client.py`
- [x] 3.2 Implement `get_chroma_client() -> chromadb.PersistentClient` singleton using `settings.GEIST_API_CHROMA_PATH`
- [x] 3.3 Ensure persistence path is created with `Path.mkdir(parents=True, exist_ok=True)` if not exists
- [x] 3.4 Implement `get_or_create_collection(name: str = "geist_chunks")` with cosine distance metadata `{"hnsw:space": "cosine"}`
- [x] 3.5 Create integration test verifying collection persists across client reinitializations

## 4. Index Manager

- [x] 4.1 Create `services/api/src/geist_api/indexing/indexer.py` with `IndexManager` class
- [x] 4.2 Implement `__init__` initializing embedder and collection
- [x] 4.3 Implement `_load_chunks(path: Path) -> list[Chunk]` loading JSONL with Pydantic validation
- [x] 4.4 Implement `_get_existing_hashes() -> set[str]` querying ChromaDB metadata for content_hash
- [x] 4.5 Implement `_index_batch(chunks: list[Chunk])` generating embeddings and calling ChromaDB `add()`
- [x] 4.6 Implement `index_chunks(chunks_jsonl_path: Path, *, incremental: bool = True) -> dict[str, int]` orchestrating load → dedupe → batch → index
- [x] 4.7 Add structlog logging for incremental_index, batch_indexed events with counts
- [x] 4.8 Configure batch size to 100 chunks per embedding call
- [x] 4.9 Create unit test with mocked ChromaDB verifying correct `add()` call structure (ids, embeddings, metadatas, documents)
- [x] 4.10 Create integration test with real ChromaDB verifying incremental indexing skips existing content_hash

## 5. CLI Entry Point

- [x] 5.1 Create `services/api/src/geist_api/cli/` package with `__init__.py`
- [x] 5.2 Create `services/api/src/geist_api/cli/index.py` with `main()` function
- [x] 5.3 Implement CLI argument parsing for `<chunks.jsonl>` positional and optional `--full` flag
- [x] 5.4 Implement file existence validation with error logging and exit code 1 on missing file
- [x] 5.5 Instantiate `IndexManager` and call `index_chunks()` with incremental flag based on `--full`
- [x] 5.6 Print summary "✓ Indexed N chunks (skipped M)" to stdout
- [x] 5.7 Add `[project.scripts]` entry point `geist-index = "geist_api.cli.index:main"` in `services/api/pyproject.toml`
- [x] 5.8 Test CLI manually: `geist-index data/test_chunks.jsonl` succeeds and prints stats

## 6. Smoke Tests

- [x] 6.1 Create `tests/integration/test_indexing_smoke.py`
- [x] 6.2 Create fixture JSONL with 10 ES chunks and 10 EN chunks from real manual excerpts
- [x] 6.3 Implement `test_smoke_bilingual_separation` indexing fixture and querying with lang filter
- [x] 6.4 Assert queries with `where={"lang": "es"}` return only ES chunks (verify metadata)
- [x] 6.5 Assert queries with `where={"lang": "en"}` return only EN chunks
- [x] 6.6 Assert no chunk_id overlap between ES and EN query results
- [x] 6.7 Run smoke tests with `just test` and verify all pass

## 7. Documentation

- [x] 7.1 Add E5 prefix requirement to `docs/base-standards.md` under "Critical Rules > Embeddings"
- [x] 7.2 Document ChromaDB persistence volume requirement in deployment section of `docs/base-standards.md`
- [x] 7.3 Add `just index` command to Justfile: `uv run geist-index data/processed/chunks_all.jsonl`
- [x] 7.4 Update README.md with model download note (~450 MB on first run)

## 8. Quality Checks

- [x] 8.1 Run `just lint` and fix any ruff violations
- [x] 8.2 Run `mypy --strict services/api/src/geist_api/indexing/` and resolve all type errors
- [x] 8.3 Run `just test` and ensure all tests pass with no warnings
- [x] 8.4 Verify coverage >85% for `indexing/` module with `pytest --cov`
- [x] 8.5 Manual verification: index real chunks JSONL and query ChromaDB directly to confirm data structure
