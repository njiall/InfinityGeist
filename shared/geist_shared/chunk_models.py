"""Pydantic models for chunks produced by ingestion pipeline."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Chunk(BaseModel):
    """A semantically coherent chunk of text from a manual with metadata.

    Chunks are the atomic unit of retrieval in the RAG system.
    """

    chunk_id: str = Field(..., description="Unique identifier for this chunk")
    canonical_rule_id: str = Field(
        ...,
        description="Deterministic ID linking ES↔EN chunks of the same rule",
    )
    lang: str = Field(..., description="Language code: 'es' or 'en'")
    manual_id: str = Field(..., description="Manual identifier (e.g., 'core', 'faq', 'its')")
    section_path: str = Field(
        ...,
        description="Normalized section path (e.g., 'rules/camouflage')",
    )
    page_start: int = Field(..., description="First page number where chunk appears", ge=1)
    page_end: int = Field(..., description="Last page number where chunk appears", ge=1)
    content: str = Field(..., description="The actual text content of the chunk", min_length=1)
    content_hash: str = Field(
        ...,
        description="SHA-256 hash of content for deduplication",
        min_length=64,
        max_length=64,
    )

    class Config:
        """Pydantic config."""

        frozen = False
        extra = "forbid"
