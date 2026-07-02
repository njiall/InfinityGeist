"""CLI entry point for the Geist ingestion pipeline.

Commands:
    extract   PDF → Markdown (TAR-01)
    chunk     Markdown → JSONL chunks (TAR-01b)
    validate  ES↔EN alignment check (TAR-01)
    pipeline  extract + chunk + validate for one manual in both languages
    orphans   Report chunks present in only one language

Examples:
    python -m geist_ingestion extract path/to/core_es.pdf --manual core --lang es
    python -m geist_ingestion chunk data/processed/es/core/content.md
    python -m geist_ingestion validate --manual core
    python -m geist_ingestion orphans --manual core
    python -m geist_ingestion pipeline --manual core --es path/es.pdf --en path/en.pdf
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import structlog

from geist_ingestion.chunk import chunk_document, report_orphans
from geist_ingestion.extract import SUPPORTED_MANUALS, extract_pdf
from geist_ingestion.validate import validate_all, validate_alignment

logger = structlog.get_logger(__name__)

DATA_DIR = Path("data/processed")
CHUNKS_DIR = Path("data/chunks")
REPORTS_DIR = Path("data/reports")


def detect_manual_from_pdf(pdf_path: str) -> str:
    """Auto-detect manual_id from PDF filename.

    Maps:
      *rules-n5* → core
      *faq-n5* → faq
      *reinforcement* → reinforcements
      *its-rules* → its (if in SUPPORTED_MANUALS)
    """
    name = Path(pdf_path).stem.lower()

    if "faq" in name:
        return "faq"
    elif "reinforcement" in name:
        return "reinforcements"
    elif "its" in name and "its" in SUPPORTED_MANUALS:
        return "its"
    else:  # default to core
        return "core"


# ---------------------------------------------------------------------------
# Sub-commands
# ---------------------------------------------------------------------------


def cmd_extract(args: argparse.Namespace) -> None:
    pdf = Path(args.pdf)
    # Auto-detect manual_id from PDF name if not provided
    manual_id = args.manual if args.manual else detect_manual_from_pdf(str(pdf))
    out = extract_pdf(
        pdf_path=pdf,
        manual_id=manual_id,
        lang=args.lang,
        output_dir=DATA_DIR,
    )
    print(f"✓ Extracted → {out}")


def cmd_chunk(args: argparse.Namespace) -> None:
    md = Path(args.markdown)
    # Infer output path from input path if not provided
    if args.output:
        out = Path(args.output)
    else:
        # data/processed/es/core/content.md → data/chunks/es/core/chunks.jsonl
        rel = md.relative_to(DATA_DIR)
        out = CHUNKS_DIR / rel.parent / "chunks.jsonl"

    chunks = chunk_document(md, out)
    print(f"✓ {len(chunks)} chunks → {out}")


def cmd_validate(args: argparse.Namespace) -> None:
    if args.manual:
        es = DATA_DIR / "es" / args.manual / "content.md"
        en = DATA_DIR / "en" / args.manual / "content.md"
        report = validate_alignment(es, en, args.manual)
        print(report.summary())
        sys.exit(1 if report.misaligned else 0)
    else:
        reports = validate_all(DATA_DIR)
        misaligned = [r for r in reports if r.misaligned]
        print(f"\n{'─'*50}")
        print(f"Total manuals: {len(reports)} | Misaligned: {len(misaligned)}")
        sys.exit(1 if misaligned else 0)


def cmd_orphans(args: argparse.Namespace) -> None:
    manual = args.manual
    es = CHUNKS_DIR / "es" / manual / "chunks.jsonl"
    en = CHUNKS_DIR / "en" / manual / "chunks.jsonl"
    out = REPORTS_DIR / manual / "orphans.json"
    orphans = report_orphans(es, en, output=out)
    if orphans:
        print(f"⚠ {len(orphans)} orphan(s) in {manual}:")
        for o in orphans:
            print(f"  [{o['missing_in'].upper()} missing] {o['canonical_rule_id']}")
        sys.exit(1)
    else:
        print(f"✓ No orphans in {manual}")


def cmd_pipeline(args: argparse.Namespace) -> None:
    """Full pipeline: extract ES + EN, chunk both, validate, report orphans."""
    manual = args.manual
    print(f"\n{'='*50}")
    print(f"Pipeline: {manual}")
    print(f"{'='*50}")

    for lang, pdf_arg in (("es", args.es), ("en", args.en)):
        pdf = Path(pdf_arg)
        print(f"\n>> Extract {lang.upper()}")
        md = extract_pdf(pdf, manual, lang, DATA_DIR)
        print(f"OK {md}")

        print(f"\n>> Chunk {lang.upper()}")
        out = CHUNKS_DIR / lang / manual / "chunks.jsonl"
        chunks = chunk_document(md, out)
        print(f"OK {len(chunks)} chunks -> {out}")

    print("\n>> Validate ES/EN")
    es_md = DATA_DIR / "es" / manual / "content.md"
    en_md = DATA_DIR / "en" / manual / "content.md"
    report = validate_alignment(es_md, en_md, manual)
    print(report.summary())

    print("\n>> Orphan report")
    es_chunks = CHUNKS_DIR / "es" / manual / "chunks.jsonl"
    en_chunks = CHUNKS_DIR / "en" / manual / "chunks.jsonl"
    orphan_out = REPORTS_DIR / manual / "orphans.json"
    orphans = report_orphans(es_chunks, en_chunks, output=orphan_out)
    if orphans:
        print(f"WARNING {len(orphans)} orphan(s) -- see {orphan_out}")
    else:
        print("OK No orphans")


# ---------------------------------------------------------------------------
# Argument parser
# ---------------------------------------------------------------------------


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="geist-ingestion",
        description="Geist ingestion pipeline — PDF extraction, chunking, validation.",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    # extract
    p_ext = sub.add_parser("extract", help="PDF → Markdown")
    p_ext.add_argument("pdf", help="Path to source PDF")
    p_ext.add_argument("--manual", choices=list(SUPPORTED_MANUALS), help="Manual ID (auto-detect from filename if omitted)")
    p_ext.add_argument("--lang", required=True, choices=["es", "en"])
    p_ext.set_defaults(func=cmd_extract)

    # chunk
    p_chunk = sub.add_parser("chunk", help="Markdown → JSONL chunks")
    p_chunk.add_argument("markdown", help="Path to content.md")
    p_chunk.add_argument("--output", help="Output JSONL path (default: derived from input)")
    p_chunk.set_defaults(func=cmd_chunk)

    # validate
    p_val = sub.add_parser("validate", help="ES↔EN alignment check")
    p_val.add_argument("--manual", help="Validate only this manual (default: all)")
    p_val.set_defaults(func=cmd_validate)

    # orphans
    p_orp = sub.add_parser("orphans", help="Report chunks missing in one language")
    p_orp.add_argument("--manual", required=True, choices=list(SUPPORTED_MANUALS))
    p_orp.set_defaults(func=cmd_orphans)

    # pipeline
    p_pip = sub.add_parser("pipeline", help="Full pipeline for one manual")
    p_pip.add_argument("--manual", required=True, choices=list(SUPPORTED_MANUALS))
    p_pip.add_argument("--es", required=True, help="Path to ES PDF")
    p_pip.add_argument("--en", required=True, help="Path to EN PDF")
    p_pip.set_defaults(func=cmd_pipeline)

    return parser


def main() -> None:
    parser = _build_parser()
    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
