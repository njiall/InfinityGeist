"""Integration tests for incremental indexing with real ChromaDB."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

# Add shared to path
shared_path = Path(__file__).resolve().parents[4] / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from geist_shared.chunk_models import Chunk

from geist_api.indexing.indexer import IndexManager


def test_incremental_indexing_skips_existing_content_hash(tmp_path: Path) -> None:
    """Verify incremental indexing skips chunks with existing content_hash."""
    # Create test JSONL with 3 chunks
    jsonl_path = tmp_path / "chunks.jsonl"
    chunks_data = [
        Chunk(
            chunk_id="chunk-001",
            canonical_rule_id="rule1",
            lang="es",
            manual_id="core",
            section_path="test/path",
            page_start=1,
            page_end=1,
            content="Content one",
            content_hash="hash1" + ("a" * 59),
        ),
        Chunk(
            chunk_id="chunk-002",
            canonical_rule_id="rule2",
            lang="en",
            manual_id="core",
            section_path="test/path",
            page_start=2,
            page_end=2,
            content="Content two",
            content_hash="hash2" + ("b" * 59),
        ),
        Chunk(
            chunk_id="chunk-003",
            canonical_rule_id="rule3",
            lang="es",
            manual_id="core",
            section_path="test/path",
            page_start=3,
            page_end=3,
            content="Content three",
            content_hash="hash3" + ("c" * 59),
        ),
    ]

    with open(jsonl_path, "w", encoding="utf-8") as f:
        for chunk in chunks_data:
            f.write(chunk.model_dump_json() + "\n")

    # Use temporary ChromaDB path
    chroma_path = tmp_path / "chroma_test"
    chroma_path.mkdir()

    # Patch settings to use test path
    from unittest.mock import patch

    with patch("geist_api.indexing.chroma_client.settings") as mock_settings:
        mock_settings.CHROMA_PATH = str(chroma_path)

        # First indexing: all 3 chunks
        indexer1 = IndexManager()
        stats1 = indexer1.index_chunks(jsonl_path, incremental=True)

        assert stats1["indexed"] == 3
        assert stats1["skipped"] == 0
        assert indexer1.collection.count() == 3

        # Second indexing: same file, should skip all 3
        indexer2 = IndexManager()
        stats2 = indexer2.index_chunks(jsonl_path, incremental=True)

        assert stats2["indexed"] == 0
        assert stats2["skipped"] == 3
        # Total count should still be 3 (no duplicates)
        assert indexer2.collection.count() == 3


def test_full_reindex_ignores_existing_hashes(tmp_path: Path) -> None:
    """Verify --full flag forces reindexing regardless of existing hashes."""
    jsonl_path = tmp_path / "chunks.jsonl"
    chunk = Chunk(
        chunk_id="chunk-001",
        canonical_rule_id="rule1",
        lang="es",
        manual_id="core",
        section_path="test",
        page_start=1,
        page_end=1,
        content="Test content",
        content_hash="testhash" + ("a" * 56),
    )

    with open(jsonl_path, "w", encoding="utf-8") as f:
        f.write(chunk.model_dump_json() + "\n")

    chroma_path = tmp_path / "chroma_test"
    chroma_path.mkdir()

    from unittest.mock import patch

    with patch("geist_api.indexing.chroma_client.settings") as mock_settings:
        mock_settings.CHROMA_PATH = str(chroma_path)

        # First index
        indexer1 = IndexManager()
        stats1 = indexer1.index_chunks(jsonl_path, incremental=True)
        assert stats1["indexed"] == 1
        assert indexer1.collection.count() == 1

        # Full reindex (incremental=False)
        indexer2 = IndexManager()
        stats2 = indexer2.index_chunks(jsonl_path, incremental=False)

        # Should index again even though hash exists
        assert stats2["indexed"] == 1
        assert stats2["skipped"] == 0
        # Note: ChromaDB will have duplicate if same ID is added twice
        # In production we'd handle this differently, but for test it shows behavior
