"""PDF → Markdown extractor.

Converts Infinity N5 PDFs to structured Markdown with YAML frontmatter.
Output: data/processed/{lang}/{manual_id}/content.md

Usage:
    python -m geist_ingestion extract <pdf_path> --manual <id> --lang <es|en>
"""

from __future__ import annotations

import hashlib
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import pymupdf4llm
import structlog

logger = structlog.get_logger(__name__)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SUPPORTED_MANUALS: dict[str, str] = {
    "core": "Infinity N5 Core Rules",
    "faq": "Infinity N5 FAQ",
    "reinforcements": "Infinity N5 Reinforcement Rules",
    "its": "ITS Season Rules",
    "annexes": "Infinity N5 Annexes",
    "qs": "Quickstart (Modiphius)",
}

# Technical acronyms that must survive normalisation unchanged
PROTECTED_TERMS = frozenset(
    [
        "CAP", "AVA", "SWC", "BS", "PH", "WIP", "ARM", "BTS", "CC",
        "MOV", "STR", "PH-6", "WIP-3", "BTS-6", "ARM-1",
        "HI", "MI", "LI", "REM", "TAG", "SK",
        "N5", "ES", "EN",
    ]
)

# Headings that signal a problematic table layout in pymupdf4llm output
_TABLE_WARN_PATTERN = re.compile(
    r"^\|[-| ]+\|$",  # divider row with only dashes — might indicate bad table
    re.MULTILINE,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def sha256_file(path: Path) -> str:
    """Return the SHA-256 hex digest of a file (for source integrity tracking)."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for block in iter(lambda: fh.read(65_536), b""):
            h.update(block)
    return h.hexdigest()


def _build_frontmatter(
    manual_id: str,
    lang: str,
    source_pdf: Path,
    pdf_hash: str,
    version: str,
    page_count: int,
) -> str:
    return (
        "---\n"
        f"manual_id: {manual_id}\n"
        f"lang: {lang}\n"
        f"manual_name: {SUPPORTED_MANUALS.get(manual_id, manual_id)}\n"
        f"source_pdf: {source_pdf.name}\n"
        f"source_pdf_hash: {pdf_hash}\n"
        f"version: {version}\n"
        f"page_count: {page_count}\n"
        f"extracted_at: {datetime.now(UTC).isoformat()}\n"
        "---\n\n"
    )


def _detect_table_issues(markdown: str) -> list[str]:
    """Return warnings for table patterns that pymupdf4llm often mangles."""
    warnings: list[str] = []

    # Tables with excessive empty cells  ← common in stat blocks
    empty_cell_ratio_threshold = 0.6
    for match in re.finditer(r"(\|[^\n]+\|\n)+", markdown):
        block = match.group()
        cells = re.findall(r"\|([^|\n]*)", block)
        if not cells:
            continue
        empty = sum(1 for c in cells if c.strip() == "")
        if empty / len(cells) > empty_cell_ratio_threshold:
            line_no = markdown[: match.start()].count("\n") + 1
            warnings.append(
                f"Line ~{line_no}: table has {empty}/{len(cells)} empty cells "
                f"({empty/len(cells):.0%}) — verify stat block extraction"
            )

    # Divider-only rows that suggest column merging failed
    for m in _TABLE_WARN_PATTERN.finditer(markdown):
        line_no = markdown[: m.start()].count("\n") + 1
        warnings.append(f"Line ~{line_no}: suspicious table divider row — may be layout artefact")

    return warnings


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract_pdf(
    pdf_path: Path,
    manual_id: str,
    lang: str,
    output_dir: Path,
    version: str = "n5",
    dpi: int = 150,
) -> Path:
    """Extract a PDF to Markdown and write it to *output_dir*.

    Args:
        pdf_path:   Absolute path to the source PDF.
        manual_id:  Short identifier from SUPPORTED_MANUALS (e.g. 'core').
        lang:       Language code: 'es' or 'en'.
        output_dir: Root data directory (e.g. Path('data/processed')).
        version:    Ruleset version tag written to frontmatter (default 'n5').
        dpi:        DPI for rasterised pages (only used when OCR fallback fires).

    Returns:
        Path to the written .md file.

    Raises:
        ValueError: if manual_id or lang are invalid.
        FileNotFoundError: if pdf_path does not exist.
    """
    if manual_id not in SUPPORTED_MANUALS:
        raise ValueError(
            f"Unknown manual_id {manual_id!r}. Valid: {list(SUPPORTED_MANUALS)}"
        )
    if lang not in ("es", "en"):
        raise ValueError(f"lang must be 'es' or 'en', got {lang!r}")
    if not pdf_path.exists():
        raise FileNotFoundError(pdf_path)

    log = logger.bind(manual=manual_id, lang=lang, pdf=pdf_path.name)
    log.info("extract.start")

    # 1. Hash the source PDF for provenance tracking
    pdf_hash = sha256_file(pdf_path)
    log.info("extract.hash", sha256=pdf_hash[:16])

    # 2. Extract via pymupdf4llm
    md_pages: list[dict[str, Any]] = pymupdf4llm.to_markdown(  # type: ignore[attr-defined]
        str(pdf_path),
        page_chunks=True,   # returns list of {text, metadata} per page
        show_progress=False,
    )

    page_count = len(md_pages)
    log.info("extract.pages", count=page_count)

    # 3. Concatenate pages, injecting page-break markers for chunk boundary hints
    parts: list[str] = []
    for page in md_pages:
        page_num: int = page.get("metadata", {}).get("page", 0) + 1
        text: str = page.get("text", "").strip()
        if text:
            parts.append(f"<!-- page:{page_num} -->\n{text}")

    body = "\n\n".join(parts)

    # 4. Detect and log table extraction issues
    table_warnings = _detect_table_issues(body)
    if table_warnings:
        log.warning(
            "extract.table_issues",
            count=len(table_warnings),
            issues=table_warnings,
        )
    else:
        log.info("extract.tables_ok")

    # 5. Assemble final document
    frontmatter = _build_frontmatter(
        manual_id=manual_id,
        lang=lang,
        source_pdf=pdf_path,
        pdf_hash=pdf_hash,
        version=version,
        page_count=page_count,
    )
    document = frontmatter + body

    # 6. Write output
    dest = output_dir / lang / manual_id / "content.md"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(document, encoding="utf-8")

    log.info("extract.done", output=str(dest), chars=len(document))
    return dest
