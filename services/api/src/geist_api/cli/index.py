"""CLI command for indexing chunks into ChromaDB."""

from __future__ import annotations

import sys
from pathlib import Path

import structlog

from geist_api.indexing.indexer import IndexManager

logger = structlog.get_logger()


def main() -> None:
    """CLI entry point for geist-index command.

    Usage:
        geist-index <chunks.jsonl>           # Incremental indexing (default)
        geist-index <chunks.jsonl> --full    # Full reindex
    """
    if len(sys.argv) < 2:
        print("Usage: geist-index <chunks.jsonl> [--full]", file=sys.stderr)
        print("\nOptions:", file=sys.stderr)
        print("  --full    Force full reindex (ignore existing content_hash)", file=sys.stderr)
        sys.exit(1)

    chunks_path = Path(sys.argv[1])
    incremental = "--full" not in sys.argv

    # Validate file exists
    if not chunks_path.exists():
        logger.error("file_not_found", path=str(chunks_path))
        print(f"Error: File not found: {chunks_path}", file=sys.stderr)
        sys.exit(1)

    if not chunks_path.is_file():
        logger.error("path_not_file", path=str(chunks_path))
        print(f"Error: Path is not a file: {chunks_path}", file=sys.stderr)
        sys.exit(1)

    try:
        # Initialize indexer and run
        indexer = IndexManager()
        stats = indexer.index_chunks(chunks_path, incremental=incremental)

        # Print summary
        mode = "incremental" if incremental else "full"
        print(f"✓ Indexed {stats['indexed']} chunks (skipped {stats['skipped']}) [{mode} mode]")
        logger.info("cli_complete", **stats, mode=mode)

    except Exception as e:
        logger.exception("indexing_failed", error=str(e))
        print(f"Error during indexing: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
