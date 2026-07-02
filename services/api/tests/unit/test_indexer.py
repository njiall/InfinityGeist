"""Unit tests for IndexManager with mocked dependencies."""

from __future__ import annotations

import sys
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

# Add shared to path
shared_path = Path(__file__).resolve().parents[4] / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from geist_shared.chunk_models import Chunk

from geist_api.indexing.indexer import IndexManager


@pytest.fixture
def mock_embedder() -> Mock:
    """Mock E5MultilingualSmall embedder."""
    embedder = Mock()
    embedder.encode_passages.return_value = [[0.1] * 384, [0.2] * 384]
    return embedder


@pytest.fixture
def mock_collection() -> Mock:
    """Mock ChromaDB collection."""
    collection = Mock()
    collection.get.return_value = {"metadatas": []}
    collection.add = Mock()
    collection.count.return_value = 0
    return collection


@pytest.fixture
def sample_chunks() -> list[Chunk]:
    """Sample chunks for testing."""
    return [
        Chunk(
            chunk_id="test-chunk-001",
            canonical_rule_id="core/camouflage/intro",
            lang="es",
            manual_id="core",
            section_path="rules/camouflage",
            page_start=42,
            page_end=42,
            content="Camuflaje otorga MOD -3 a tiradas de ataque.",
            content_hash="a" * 64,
        ),
        Chunk(
            chunk_id="test-chunk-002",
            canonical_rule_id="core/camouflage/intro",
            lang="en",
            manual_id="core",
            section_path="rules/camouflage",
            page_start=42,
            page_end=42,
            content="Camouflage grants MOD -3 to attack rolls.",
            content_hash="b" * 64,
        ),
    ]


def test_index_batch_calls_chromadb_correctly(
    mock_embedder: Mock,
    mock_collection: Mock,
    sample_chunks: list[Chunk],
) -> None:
    """Verify _index_batch calls ChromaDB add() with correct structure."""
    with (
        patch("geist_api.indexing.indexer.E5MultilingualSmall", return_value=mock_embedder),
        patch("geist_api.indexing.indexer.get_or_create_collection", return_value=mock_collection),
    ):
        indexer = IndexManager()
        indexer._index_batch(sample_chunks)

        # Verify embedder was called with chunk contents
        mock_embedder.encode_passages.assert_called_once()
        texts_arg = mock_embedder.encode_passages.call_args[0][0]
        assert len(texts_arg) == 2
        assert "Camuflaje otorga MOD -3" in texts_arg[0]
        assert "Camouflage grants MOD -3" in texts_arg[1]

        # Verify ChromaDB add() was called with correct structure
        mock_collection.add.assert_called_once()
        call_kwargs = mock_collection.add.call_args.kwargs

        assert "ids" in call_kwargs
        assert call_kwargs["ids"] == ["test-chunk-001", "test-chunk-002"]

        assert "embeddings" in call_kwargs
        assert len(call_kwargs["embeddings"]) == 2

        assert "metadatas" in call_kwargs
        metadatas = call_kwargs["metadatas"]
        assert len(metadatas) == 2
        assert metadatas[0]["lang"] == "es"
        assert metadatas[0]["content_hash"] == "a" * 64
        assert metadatas[1]["lang"] == "en"

        assert "documents" in call_kwargs
        assert len(call_kwargs["documents"]) == 2


def test_get_existing_hashes_queries_metadata(
    mock_embedder: Mock,
    mock_collection: Mock,
) -> None:
    """Verify _get_existing_hashes queries ChromaDB metadata correctly."""
    mock_collection.get.return_value = {
        "metadatas": [
            {"content_hash": "hash1"},
            {"content_hash": "hash2"},
            {"content_hash": "hash3"},
        ],
    }

    with (
        patch("geist_api.indexing.indexer.E5MultilingualSmall", return_value=mock_embedder),
        patch("geist_api.indexing.indexer.get_or_create_collection", return_value=mock_collection),
    ):
        indexer = IndexManager()
        hashes = indexer._get_existing_hashes()

        # Verify ChromaDB was queried for metadatas
        mock_collection.get.assert_called_once_with(include=["metadatas"])

        # Verify hashes were extracted correctly
        assert hashes == {"hash1", "hash2", "hash3"}


def test_get_existing_hashes_handles_empty_collection(
    mock_embedder: Mock,
    mock_collection: Mock,
) -> None:
    """Verify _get_existing_hashes handles empty collection."""
    mock_collection.get.return_value = {"metadatas": []}

    with (
        patch("geist_api.indexing.indexer.E5MultilingualSmall", return_value=mock_embedder),
        patch("geist_api.indexing.indexer.get_or_create_collection", return_value=mock_collection),
    ):
        indexer = IndexManager()
        hashes = indexer._get_existing_hashes()

        assert hashes == set()


def test_load_chunks_validates_with_pydantic(tmp_path: Path) -> None:
    """Verify _load_chunks uses Pydantic validation."""
    jsonl_path = tmp_path / "chunks.jsonl"

    # Write valid JSONL
    jsonl_path.write_text(
        '{"chunk_id":"id1","canonical_rule_id":"rule1","lang":"es","manual_id":"core",'
        '"section_path":"test","page_start":1,"page_end":1,"content":"Test",'
        '"content_hash":"' + ("a" * 64) + '"}\n'
        '{"chunk_id":"id2","canonical_rule_id":"rule2","lang":"en","manual_id":"core",'
        '"section_path":"test","page_start":2,"page_end":2,"content":"Test2",'
        '"content_hash":"' + ("b" * 64) + '"}\n',
        encoding="utf-8",
    )

    with (
        patch("geist_api.indexing.indexer.E5MultilingualSmall"),
        patch("geist_api.indexing.indexer.get_or_create_collection"),
    ):
        indexer = IndexManager()
        chunks = indexer._load_chunks(jsonl_path)

        assert len(chunks) == 2
        assert all(isinstance(c, Chunk) for c in chunks)
        assert chunks[0].chunk_id == "id1"
        assert chunks[1].chunk_id == "id2"
