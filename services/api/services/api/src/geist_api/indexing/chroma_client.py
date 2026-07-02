"""ChromaDB client singleton for persistent vector storage."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

import chromadb

from geist_api.settings import settings  # type: ignore[import-untyped]

if TYPE_CHECKING:
    from chromadb.api import Collection  # type: ignore[attr-defined]

# Module-level singleton
_client: Any | None = None


def get_chroma_client() -> Any:
    """Get or create ChromaDB PersistentClient singleton.

    Uses path from settings.CHROMA_PATH (default: "data/chroma").
    Creates directory if it doesn't exist.

    Returns:
        ChromaDB PersistentClient instance
    """
    global _client  # noqa: PLW0603
    if _client is None:
        persist_path = Path(settings.CHROMA_PATH)
        persist_path.mkdir(parents=True, exist_ok=True)
        _client = chromadb.PersistentClient(path=str(persist_path))
    return _client


def get_or_create_collection(name: str = "geist_chunks") -> Any:
    """Get or create a ChromaDB collection with cosine distance.

    Args:
        name: Collection name (default: "geist_chunks")

    Returns:
        ChromaDB Collection instance configured for cosine similarity
    """
    client = get_chroma_client()
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},  # Cosine distance for similarity search
    )
