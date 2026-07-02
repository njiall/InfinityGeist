"""Smoke tests for bilingual indexing and retrieval."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path

import pytest

# Add shared to path
shared_path = Path(__file__).resolve().parents[4] / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from geist_api.indexing.chroma_client import get_or_create_collection
from geist_api.indexing.embedder import E5MultilingualSmall
from geist_api.indexing.indexer import IndexManager


@pytest.fixture(scope="module")
def smoke_fixture_path() -> Path:
    """Path to smoke test JSONL fixture."""
    return Path(__file__).parent.parent / "fixtures" / "smoke_chunks.jsonl"


@pytest.fixture(scope="module")
def indexed_collection(smoke_fixture_path: Path):
    """Index smoke chunks once for all tests in this module."""
    with tempfile.TemporaryDirectory() as tmpdir:
        chroma_path = Path(tmpdir) / "chroma_smoke"
        chroma_path.mkdir()

        from unittest.mock import patch

        with patch("geist_api.indexing.chroma_client.settings") as mock_settings:
            mock_settings.CHROMA_PATH = str(chroma_path)

            # Index the fixture
            indexer = IndexManager()
            stats = indexer.index_chunks(smoke_fixture_path, incremental=False)

            print(f"\nIndexed {stats['indexed']} smoke test chunks")

            yield indexer.collection


def test_smoke_bilingual_separation(indexed_collection, smoke_fixture_path: Path) -> None:
    """Verify queries with lang filter return only chunks in that language."""
    embedder = E5MultilingualSmall()

    # Query in Spanish about camouflage
    query_es = embedder.encode_query("cómo funciona camuflaje")
    results_es = indexed_collection.query(
        query_embeddings=[query_es],
        n_results=3,
        where={"lang": "es"},
    )

    # All results should be Spanish
    assert len(results_es["ids"][0]) == 3
    for metadata in results_es["metadatas"][0]:
        assert metadata["lang"] == "es", f"Expected ES but got {metadata['lang']}"

    # Query in English about camouflage
    query_en = embedder.encode_query("how does camouflage work")
    results_en = indexed_collection.query(
        query_embeddings=[query_en],
        n_results=3,
        where={"lang": "en"},
    )

    # All results should be English
    assert len(results_en["ids"][0]) == 3
    for metadata in results_en["metadatas"][0]:
        assert metadata["lang"] == "en", f"Expected EN but got {metadata['lang']}"


def test_smoke_no_chunk_id_overlap(indexed_collection) -> None:
    """Verify ES and EN queries return different chunk_ids (no contamination)."""
    embedder = E5MultilingualSmall()

    query_es = embedder.encode_query("combate cuerpo a cuerpo")
    results_es = indexed_collection.query(
        query_embeddings=[query_es],
        n_results=5,
        where={"lang": "es"},
    )

    query_en = embedder.encode_query("close combat")
    results_en = indexed_collection.query(
        query_embeddings=[query_en],
        n_results=5,
        where={"lang": "en"},
    )

    ids_es = set(results_es["ids"][0])
    ids_en = set(results_en["ids"][0])

    # No overlap between Spanish and English results
    assert ids_es.isdisjoint(ids_en), "ES and EN queries returned overlapping chunk_ids"


def test_smoke_metadata_preserved(indexed_collection) -> None:
    """Verify all metadata fields are preserved in ChromaDB."""
    results = indexed_collection.get(ids=["smoke-es-001"])

    assert len(results["ids"]) == 1
    metadata = results["metadatas"][0]

    # Check all required metadata fields
    assert metadata["lang"] == "es"
    assert metadata["manual_id"] == "core"
    assert metadata["canonical_rule_id"] == "core/camouflage/intro"
    assert metadata["section_path"] == "rules/camouflage"
    assert metadata["page_start"] == 42
    assert metadata["page_end"] == 42
    assert metadata["content_hash"] == "1" * 64

    # Check document content
    assert len(results["documents"]) == 1
    assert "Camuflaje" in results["documents"][0]
    assert "MOD -3" in results["documents"][0]


def test_smoke_semantic_search_es(indexed_collection) -> None:
    """Verify semantic search finds relevant chunks in Spanish."""
    embedder = E5MultilingualSmall()

    query = embedder.encode_query("reacción automática durante turno enemigo")
    results = indexed_collection.query(
        query_embeddings=[query],
        n_results=1,
        where={"lang": "es"},
    )

    # Should find ARO chunk
    assert len(results["ids"][0]) == 1
    doc = results["documents"][0][0]
    assert "ARO" in doc or "Automatic Reaction" in doc


def test_smoke_semantic_search_en(indexed_collection) -> None:
    """Verify semantic search finds relevant chunks in English."""
    embedder = E5MultilingualSmall()

    query = embedder.encode_query("team coordination bonuses")
    results = indexed_collection.query(
        query_embeddings=[query],
        n_results=1,
        where={"lang": "en"},
    )

    # Should find Fireteam chunk
    assert len(results["ids"][0]) == 1
    doc = results["documents"][0][0]
    assert "Fireteam" in doc or "coordination" in doc or "bonuses" in doc
