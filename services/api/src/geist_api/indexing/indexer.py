"""Index manager for chunked documents."""

from __future__ import annotations

import sys
from pathlib import Path

import structlog

# Add shared package to Python path if not already there
shared_path = Path(__file__).resolve().parents[5] / "shared"
if str(shared_path) not in sys.path:
    sys.path.insert(0, str(shared_path))

from geist_shared.chunk_models import Chunk

from geist_api.indexing.chroma_client import get_or_create_collection
from geist_api.indexing.embedder import E5MultilingualSmall

logger = structlog.get_logger()

# Batch size for embedding generation
BATCH_SIZE = 100


class IndexManager:
    """Manages indexing of chunks into ChromaDB with E5 embeddings."""

    def __init__(self) -> None:
        """Initialize embedder and ChromaDB collection."""
        self.embedder = E5MultilingualSmall()
        self.collection = get_or_create_collection()

    def index_chunks(
        self,
        chunks_jsonl_path: Path,
        *,
        incremental: bool = True,
    ) -> dict[str, int]:
        """Index chunks from JSONL file into ChromaDB.

        Args:
            chunks_jsonl_path: Path to JSONL file containing chunks
            incremental: If True, skip chunks already indexed by content_hash

        Returns:
            Dict with 'indexed' and 'skipped' counts
        """
        chunks = self._load_chunks(chunks_jsonl_path)
        logger.info("chunks_loaded", path=str(chunks_jsonl_path), total=len(chunks))

        if incremental:
            existing_hashes = self._get_existing_hashes()
            original_count = len(chunks)
            chunks = [c for c in chunks if c.content_hash not in existing_hashes]
            skipped = original_count - len(chunks)
            logger.info(
                "incremental_index",
                total=len(chunks),
                skipped=skipped,
            )
        else:
            skipped = 0

        if not chunks:
            return {"indexed": 0, "skipped": skipped}

        # Batch processing
        indexed = 0
        for i in range(0, len(chunks), BATCH_SIZE):
            batch = chunks[i : i + BATCH_SIZE]
            self._index_batch(batch)
            indexed += len(batch)

        logger.info("indexing_complete", indexed=indexed, skipped=skipped)
        return {"indexed": indexed, "skipped": skipped}

    def _load_chunks(self, path: Path) -> list[Chunk]:
        """Load chunks from JSONL file with Pydantic validation.

        Args:
            path: Path to JSONL file

        Returns:
            List of validated Chunk objects
        """
        chunks: list[Chunk] = []
        with open(path, encoding="utf-8") as f:
            for line_num, line in enumerate(f, start=1):
                line = line.strip()
                if not line:
                    continue
                try:
                    chunk = Chunk.model_validate_json(line)
                    chunks.append(chunk)
                except Exception as e:
                    logger.error(
                        "chunk_validation_failed",
                        line_num=line_num,
                        error=str(e),
                    )
                    raise
        return chunks

    def _get_existing_hashes(self) -> set[str]:
        """Query ChromaDB for existing content_hash values.

        Returns:
            Set of content_hash strings already in the index
        """
        results = self.collection.get(include=["metadatas"])
        hashes = {
            meta["content_hash"]
            for meta in results["metadatas"]
            if meta and "content_hash" in meta
        }
        logger.debug("existing_hashes_retrieved", count=len(hashes))
        return hashes

    def _index_batch(self, chunks: list[Chunk]) -> None:
        """Index a batch of chunks into ChromaDB.

        Args:
            chunks: Batch of chunks to index
        """
        texts = [c.content for c in chunks]
        embeddings = self.embedder.encode_passages(texts)

        ids = [c.chunk_id for c in chunks]
        metadatas = [
            {
                "lang": c.lang,
                "manual_id": c.manual_id,
                "canonical_rule_id": c.canonical_rule_id,
                "section_path": c.section_path,
                "page_start": c.page_start,
                "page_end": c.page_end,
                "content_hash": c.content_hash,
            }
            for c in chunks
        ]
        documents = texts

        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            metadatas=metadatas,
            documents=documents,
        )

        logger.info("batch_indexed", count=len(chunks))
