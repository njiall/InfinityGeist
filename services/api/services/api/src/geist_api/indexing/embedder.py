"""E5 multilingual embedding model wrapper with mandatory prefix enforcement.

CRITICAL: E5 models REQUIRE "passage:" and "query:" prefixes. Without them,
retrieval quality degrades by 20-30%. This wrapper enforces correct usage.
"""

from __future__ import annotations

from typing import Protocol

from sentence_transformers import SentenceTransformer


class EmbeddingModel(Protocol):
    """Protocol for embedding models."""

    def encode_passages(self, texts: list[str]) -> list[list[float]]:
        """Encode passages for indexing."""
        ...

    def encode_query(self, text: str) -> list[float]:
        """Encode query for retrieval."""
        ...


class E5MultilingualSmall:
    """Wrapper for intfloat/multilingual-e5-small with mandatory prefix enforcement.

    MANDATORY / OBLIGATORIO:
    - Passages MUST be prefixed with "passage: " during indexing
    - Queries MUST be prefixed with "query: " during retrieval
    - Without prefixes, recall drops 20-30% (documented in E5 paper)

    This wrapper enforces correct prefix usage via separate encode methods.
    DO NOT bypass this wrapper by using the underlying model directly.
    """

    def __init__(self) -> None:
        """Load intfloat/multilingual-e5-small model (118M params, ~450 MB download)."""
        self.model = SentenceTransformer("intfloat/multilingual-e5-small")

    def encode_passages(self, texts: list[str]) -> list[list[float]]:
        """Encode passages for indexing.

        MANDATORY: Adds "passage: " prefix to each text before encoding.

        Args:
            texts: List of passage texts to encode

        Returns:
            List of embedding vectors (each 384 dimensions)
        """
        prefixed = [f"passage: {text}" for text in texts]
        embeddings = self.model.encode(prefixed, show_progress_bar=True, convert_to_numpy=False)
        return [emb.tolist() for emb in embeddings]

    def encode_query(self, text: str) -> list[float]:
        """Encode query for retrieval.

        MANDATORY: Adds "query: " prefix before encoding.

        Args:
            text: Query text to encode

        Returns:
            Embedding vector (384 dimensions)
        """
        prefixed = f"query: {text}"
        embedding = self.model.encode(prefixed, convert_to_numpy=False)
        return embedding.tolist()  # type: ignore[no-any-return]
