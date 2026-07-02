## ADDED Requirements

### Requirement: Deduplicate by content hash

The system SHALL skip indexing chunks whose content_hash already exists in ChromaDB metadata, enabling efficient incremental updates.

#### Scenario: Skip existing chunks
- **WHEN** ChromaDB contains chunk with content_hash "abc123"
- **AND** JSONL file includes chunk with same content_hash "abc123"
- **THEN** system skips embedding generation for that chunk
- **AND** stats report skipped count incremented by 1
- **AND** indexed count not incremented

#### Scenario: Index new chunks only
- **WHEN** ChromaDB contains 100 chunks with known hashes
- **AND** JSONL file contains 120 chunks (100 existing + 20 new)
- **THEN** system generates embeddings for only 20 new chunks
- **AND** stats report indexed=20, skipped=100

#### Scenario: First indexing run
- **WHEN** ChromaDB collection is empty
- **AND** JSONL file contains 500 chunks
- **THEN** system indexes all 500 chunks
- **AND** stats report indexed=500, skipped=0

### Requirement: Content hash validation

The system SHALL use SHA-256 content_hash field from chunk metadata as deduplication key.

#### Scenario: Hash-based identity
- **WHEN** two chunks have identical content but different chunk_id
- **AND** both have same content_hash
- **THEN** only first chunk is indexed
- **AND** second chunk is skipped as duplicate

#### Scenario: Changed content reindexing
- **WHEN** chunk with chunk_id "core-es-001" was previously indexed with content_hash "hash_v1"
- **AND** same chunk_id appears in JSONL with updated content_hash "hash_v2"
- **THEN** system indexes the new version with hash_v2
- **AND** both versions exist in ChromaDB with different hashes

### Requirement: Full reindex override

The system SHALL support `--full` flag to force reindexing all chunks regardless of existing content_hash.

#### Scenario: Full reindex ignores existing hashes
- **WHEN** ChromaDB contains 100 chunks
- **AND** user runs `geist-index data/chunks.jsonl --full`
- **AND** JSONL contains same 100 chunks
- **THEN** system reindexes all 100 chunks
- **AND** stats report indexed=100, skipped=0

#### Scenario: Full reindex use case
- **WHEN** embedding model is upgraded from E5-small to E5-large
- **AND** user needs to regenerate all embeddings
- **THEN** `--full` flag forces complete reindexing
- **AND** existing vectors are replaced with new model outputs

### Requirement: Incremental indexing performance

The system SHALL query existing content_hash values in under 1 second for collections up to 10,000 chunks.

#### Scenario: Fast hash lookup
- **WHEN** ChromaDB contains 10,000 indexed chunks
- **AND** system queries all content_hash metadata
- **THEN** query completes in under 1000ms
- **AND** returned set contains 10,000 unique hashes

#### Scenario: Memory efficiency
- **WHEN** querying existing hashes for collection with 10,000 chunks
- **THEN** memory usage for hash set is under 2 MB
- **AND** system does not load full chunk documents into memory
