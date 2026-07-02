"""Integration tests for ChromaDB persistence."""

from __future__ import annotations

import tempfile
from pathlib import Path

import chromadb


def test_collection_persists_across_reinitializations() -> None:
    """Verify that ChromaDB collection persists when client is recreated."""
    with tempfile.TemporaryDirectory() as tmpdir:
        persist_path = Path(tmpdir) / "chroma_test"
        persist_path.mkdir(parents=True, exist_ok=True)

        # First client: create collection and add data
        client1 = chromadb.PersistentClient(path=str(persist_path))
        collection1 = client1.get_or_create_collection(
            name="test_collection",
            metadata={"hnsw:space": "cosine"},
        )

        # Add test data
        collection1.add(
            ids=["test_id_1", "test_id_2"],
            embeddings=[[0.1] * 384, [0.2] * 384],
            metadatas=[{"lang": "es"}, {"lang": "en"}],
            documents=["Test document 1", "Test document 2"],
        )

        # Verify data was added
        count1 = collection1.count()
        assert count1 == 2

        # Simulate process restart: create new client instance
        del client1, collection1

        client2 = chromadb.PersistentClient(path=str(persist_path))
        collection2 = client2.get_or_create_collection(
            name="test_collection",
            metadata={"hnsw:space": "cosine"},
        )

        # Verify data persisted
        count2 = collection2.count()
        assert count2 == 2, "Collection should persist across client restarts"

        # Verify can retrieve data
        results = collection2.get(ids=["test_id_1"])
        assert results["ids"] == ["test_id_1"]
        assert results["documents"] == ["Test document 1"]
        assert results["metadatas"] == [{"lang": "es"}]


def test_multiple_collections_in_same_client() -> None:
    """Verify multiple collections can coexist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        persist_path = Path(tmpdir) / "chroma_test"
        persist_path.mkdir(parents=True, exist_ok=True)

        client = chromadb.PersistentClient(path=str(persist_path))

        # Create two collections
        col1 = client.get_or_create_collection("collection_1")
        col2 = client.get_or_create_collection("collection_2")

        # Add data to each
        col1.add(ids=["id1"], embeddings=[[0.1] * 384], documents=["Doc 1"])
        col2.add(ids=["id2"], embeddings=[[0.2] * 384], documents=["Doc 2"])

        # Verify isolation
        assert col1.count() == 1
        assert col2.count() == 1
        assert col1.get(ids=["id1"])["documents"] == ["Doc 1"]
        assert col2.get(ids=["id2"])["documents"] == ["Doc 2"]
