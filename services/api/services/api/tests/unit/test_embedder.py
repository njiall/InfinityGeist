"""Unit tests for E5 embedding wrapper."""

from __future__ import annotations

import math

import pytest
from geist_api.indexing.embedder import E5MultilingualSmall


def cosine_similarity(a: list[float], b: list[float]) -> float:
    """Compute cosine similarity between two vectors."""
    dot_product = sum(x * y for x, y in zip(a, b, strict=True))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    return dot_product / (norm_a * norm_b)


@pytest.fixture(scope="module")
def embedder() -> E5MultilingualSmall:
    """Shared embedder instance for all tests (model loading is expensive)."""
    return E5MultilingualSmall()


def test_encode_passages_returns_correct_shape(embedder: E5MultilingualSmall) -> None:
    """Test that encode_passages returns list of 384-dim vectors."""
    texts = ["Test passage one", "Test passage two"]
    embeddings = embedder.encode_passages(texts)

    assert len(embeddings) == 2
    assert all(len(emb) == 384 for emb in embeddings)
    assert all(isinstance(emb, list) for emb in embeddings)
    assert all(isinstance(v, float) for emb in embeddings for v in emb)


def test_encode_query_returns_correct_shape(embedder: E5MultilingualSmall) -> None:
    """Test that encode_query returns single 384-dim vector."""
    text = "Test query"
    embedding = embedder.encode_query(text)

    assert len(embedding) == 384
    assert isinstance(embedding, list)
    assert all(isinstance(v, float) for v in embedding)


def test_prefixed_vs_non_prefixed_differ(embedder: E5MultilingualSmall) -> None:
    """Verify that prefixes change embedding (critical for quality).

    Without prefixes, E5 quality drops 20-30%. This test ensures the wrapper
    is applying prefixes correctly by comparing against non-prefixed encoding.
    """
    text = "Camuflaje otorga MOD -3 a tiradas de ataque"

    # Get prefixed embedding (via wrapper)
    prefixed_emb = embedder.encode_passages([text])[0]

    # Get non-prefixed embedding (direct model access, for test only)
    non_prefixed_emb = embedder.model.encode(text, convert_to_numpy=False).tolist()

    # Cosine similarity should be <0.9 if prefixes are working
    similarity = cosine_similarity(prefixed_emb, non_prefixed_emb)
    assert similarity < 0.9, (
        f"Prefixed and non-prefixed embeddings too similar ({similarity:.3f}). "
        "Prefixes may not be applied correctly!"
    )


def test_query_vs_passage_encoding_differ(embedder: E5MultilingualSmall) -> None:
    """Verify that query and passage encoding produce different embeddings.

    E5 is trained with asymmetric encoding (query vs passage). This test
    ensures the wrapper is applying different prefixes correctly.
    """
    text = "Cómo funciona el camuflaje en Infinity"

    query_emb = embedder.encode_query(text)
    passage_emb = embedder.encode_passages([text])[0]

    similarity = cosine_similarity(query_emb, passage_emb)
    assert similarity < 0.95, (
        f"Query and passage embeddings too similar ({similarity:.3f}). "
        "Asymmetric encoding may not be working!"
    )


def test_encode_passages_batch_consistency(embedder: E5MultilingualSmall) -> None:
    """Test that batching produces consistent results."""
    texts = ["First text", "Second text", "Third text"]

    # Encode as batch
    batch_emb = embedder.encode_passages(texts)

    # Encode individually
    individual_emb = [embedder.encode_passages([t])[0] for t in texts]

    # Should be very similar (allowing for floating point rounding)
    for batch, individual in zip(batch_emb, individual_emb, strict=True):
        similarity = cosine_similarity(batch, individual)
        assert similarity > 0.99, "Batch and individual encoding should be nearly identical"


def test_multilingual_support(embedder: E5MultilingualSmall) -> None:
    """Test that model handles ES and EN text."""
    texts_es = ["Camuflaje otorga MOD -3"]
    texts_en = ["Camouflage grants MOD -3"]

    emb_es = embedder.encode_passages(texts_es)
    emb_en = embedder.encode_passages(texts_en)

    # Both should produce valid embeddings
    assert len(emb_es[0]) == 384
    assert len(emb_en[0]) == 384

    # Semantic similarity should be high (same meaning in different languages)
    similarity = cosine_similarity(emb_es[0], emb_en[0])
    assert similarity > 0.7, "Semantically equivalent ES/EN text should have high similarity"
