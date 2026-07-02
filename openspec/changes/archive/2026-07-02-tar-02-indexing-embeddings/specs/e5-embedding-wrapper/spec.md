## ADDED Requirements

### Requirement: Enforce E5 passage prefix

The system SHALL prepend "passage: " to all chunk texts before generating embeddings for indexing, as required by E5 model training.

#### Scenario: Passage prefix applied during indexing
- **WHEN** system indexes chunk with content "Camuflaje otorga MOD -3"
- **THEN** text passed to E5 model is "passage: Camuflaje otorga MOD -3"
- **AND** embedding vector is generated from prefixed text

#### Scenario: Batch passage prefix
- **WHEN** system indexes batch of 100 chunks
- **THEN** all 100 texts have "passage: " prefix applied
- **AND** model.encode() receives list of 100 prefixed strings

### Requirement: Enforce E5 query prefix

The system SHALL prepend "query: " to all user queries before generating query embeddings for retrieval.

#### Scenario: Query prefix applied during search
- **WHEN** user searches for "cómo funciona camuflaje"
- **THEN** text passed to E5 model is "query: cómo funciona camuflaje"
- **AND** query embedding is generated from prefixed text

### Requirement: Wrapper API separation

The system SHALL provide separate methods `encode_passages()` and `encode_query()` to enforce correct prefix usage and prevent misuse.

#### Scenario: Passage encoding API
- **WHEN** caller invokes `embedder.encode_passages(["text1", "text2"])`
- **THEN** method returns list of 2 embedding vectors
- **AND** each vector has dimension 384
- **AND** prefixes were applied internally without caller action

#### Scenario: Query encoding API
- **WHEN** caller invokes `embedder.encode_query("search text")`
- **THEN** method returns single embedding vector of dimension 384
- **AND** "query: " prefix was applied internally

#### Scenario: No generic encode method
- **WHEN** developer attempts to access generic `encode()` method
- **THEN** only `encode_passages()` and `encode_query()` are exposed in wrapper API
- **AND** direct model access is encapsulated

### Requirement: Prefix impact verification

The system SHALL include test verifying that embeddings with and without prefixes produce meaningfully different vectors.

#### Scenario: Prefix quality test
- **WHEN** test generates embedding for "passage: test text"
- **AND** test generates embedding for "test text" (no prefix)
- **THEN** cosine similarity between vectors is less than 0.90
- **AND** test passes, confirming prefix changes embedding space

#### Scenario: Query-passage asymmetry test
- **WHEN** test encodes same text with `encode_passages()` and `encode_query()`
- **THEN** resulting vectors are different
- **AND** cosine similarity is less than 0.95
- **AND** asymmetric encoding is confirmed working

### Requirement: Model initialization

The system SHALL load `intfloat/multilingual-e5-small` from HuggingFace on first use, caching model weights locally.

#### Scenario: First-time model download
- **WHEN** E5MultilingualSmall is instantiated for first time
- **THEN** system downloads model from HuggingFace hub
- **AND** model weights are cached at `~/.cache/huggingface/`
- **AND** subsequent instantiations reuse cached weights

#### Scenario: Offline mode after download
- **WHEN** model has been downloaded once
- **AND** `TRANSFORMERS_OFFLINE=1` environment variable is set
- **THEN** model loads from local cache without network request
- **AND** initialization completes in under 2 seconds

### Requirement: Embedding output format

The system SHALL return embeddings as Python list of floats (not numpy arrays) for ChromaDB compatibility.

#### Scenario: Output format for ChromaDB
- **WHEN** `encode_passages()` generates embeddings
- **THEN** return type is `list[list[float]]`
- **AND** each inner list has length 384
- **AND** format is directly compatible with ChromaDB `add()` method

#### Scenario: Single query output format
- **WHEN** `encode_query()` generates embedding
- **THEN** return type is `list[float]`
- **AND** list has length 384
- **AND** format is directly compatible with ChromaDB `query()` method
