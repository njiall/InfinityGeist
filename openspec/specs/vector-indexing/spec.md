## ADDED Requirements

### Requirement: Index chunks with multilingual embeddings

The system SHALL index chunks from JSONL files into ChromaDB with embeddings from `intfloat/multilingual-e5-small`, preserving all metadata fields required for retrieval and citation.

#### Scenario: Successful indexing of bilingual chunks
- **WHEN** `geist-index` processes a JSONL file containing ES and EN chunks with complete metadata
- **THEN** ChromaDB collection contains entries with embeddings, documents, and metadata for lang, manual_id, canonical_rule_id, section_path, page_start, page_end, content_hash

#### Scenario: Chunks are indexed with correct embeddings
- **WHEN** system indexes chunk text "Camuflaje TO otorga MOD -3 a BS"
- **THEN** embedding vector is generated with "passage: " prefix applied
- **AND** vector dimension matches model output (384 dims for E5-small)

### Requirement: ChromaDB persistence

The system SHALL use ChromaDB PersistentClient with configurable path to ensure index survives process restarts and redeployments.

#### Scenario: Index persists across restarts
- **WHEN** chunks are indexed to ChromaDB at path `data/chroma`
- **AND** API process restarts
- **THEN** ChromaDB client reconnects to existing collection without re-indexing
- **AND** all previously indexed chunks remain queryable

#### Scenario: Custom persistence path
- **WHEN** `GEIST_API_CHROMA_PATH` environment variable is set to `/mnt/vector-db`
- **THEN** ChromaDB stores collection data at `/mnt/vector-db/chroma.sqlite3`

### Requirement: Bilingual metadata filtering

The system SHALL store language metadata with each chunk to enable query-time filtering without cross-language contamination.

#### Scenario: Language filtering in ChromaDB
- **WHEN** collection contains chunks with `lang=es` and `lang=en`
- **AND** system queries with filter `where={"lang": "es"}`
- **THEN** results contain only chunks where metadata lang equals "es"
- **AND** no chunks with `lang=en` are returned

### Requirement: Batch processing for efficiency

The system SHALL index chunks in configurable batches to optimize embedding generation and ChromaDB insert performance.

#### Scenario: Batch indexing
- **WHEN** indexing 500 chunks with batch size 100
- **THEN** system processes exactly 5 batches
- **AND** each batch generates embeddings for 100 texts in parallel
- **AND** total indexing time is less than 10 minutes on modern CPU

#### Scenario: Empty input handling
- **WHEN** JSONL file contains 0 chunks
- **THEN** indexing completes without error
- **AND** stats report 0 indexed, 0 skipped

### Requirement: CLI entry point

The system SHALL provide a `geist-index` CLI command accepting JSONL file path and optional `--full` flag.

#### Scenario: CLI success
- **WHEN** user runs `geist-index data/chunks.jsonl`
- **THEN** command indexes all chunks incrementally
- **AND** prints summary: "✓ Indexed N chunks (skipped M)"
- **AND** exits with code 0

#### Scenario: CLI file not found
- **WHEN** user runs `geist-index nonexistent.jsonl`
- **THEN** command logs error "file_not_found" with path
- **AND** prints error message to stderr
- **AND** exits with code 1

#### Scenario: CLI full reindex flag
- **WHEN** user runs `geist-index data/chunks.jsonl --full`
- **THEN** system reindexes all chunks regardless of existing content_hash
- **AND** stats report all chunks as indexed, 0 skipped
