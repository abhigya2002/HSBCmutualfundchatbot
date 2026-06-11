"""
Phase 2.4 — Normalize Phase 2.3 extracted HTML to Markdown under ``artifacts/clean/``.

Requires ``artifacts/extracted/*.main.html``. Run from ``phases/phase-2-ingestion``::

    python -m phase_2_4.run_normalize
"""

from __future__ import annotations

import argparse
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

from common.config import load_config, phase2_ingestion_root
from common.logging_setup import setup_ingestion_logging
from common.paths import ArtifactPaths
from common.registry_bridge import validate_registry_or_raise

from phase_2_4.normalize import NORMALIZER_VERSION, build_corpus_boilerplate_lines, normalize_extracted_html

log = logging.getLogger("phase2_ingestion.phase_2_4")


def _min_corpus_coverage(n_docs: int) -> int:
    """How many documents a line must appear in to be treated as corpus boilerplate."""
    if n_docs <= 1:
        return 1
    return max(2, min(15, n_docs - 1))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2.4 — normalize extracted HTML to clean Markdown.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    parser.add_argument(
        "--no-corpus-dedupe",
        action="store_true",
        help="Skip cross-document repeated-line removal (single-doc runs).",
    )
    args = parser.parse_args(argv)

    phase2_root = phase2_ingestion_root()
    config = load_config(args.config)
    setup_ingestion_logging(config)
    paths = ArtifactPaths.from_config(config, phase2_root)
    paths.ensure_dirs()

    registry = validate_registry_or_raise()
    entries = sorted(registry["entries"], key=lambda e: int(e["id"]))

    payloads: list[tuple[str, str, Path, Path, bytes, dict[str, object]]] = []
    for entry in entries:
        slug = str(entry["scheme"])
        url = str(entry["url"])
        main_path = paths.extracted_main_html_path(slug)
        ext_path = paths.extract_sidecar_path(slug)
        extract_meta: dict[str, object] = {}
        if ext_path.exists():
            try:
                extract_meta = json.loads(ext_path.read_text(encoding="utf-8"))
            except Exception:
                extract_meta = {"extract_status": "sidecar_read_error"}
        if not main_path.exists():
            log.error("Missing extracted main HTML for %s (%s)", slug, main_path)
            payloads.append((slug, url, main_path, ext_path, b"", extract_meta))
            continue
        payloads.append((slug, url, main_path, ext_path, main_path.read_bytes(), extract_meta))

    blocklist: frozenset[str] = frozenset()
    if not args.no_corpus_dedupe:
        first_mds: list[str] = []
        for _slug, _url, _mp, _ep, html_bytes, _em in payloads:
            if not html_bytes:
                first_mds.append("")
                continue
            first_mds.append(normalize_extracted_html(html_bytes, corpus_line_blocklist=None).markdown)
        n_ok = sum(1 for m in first_mds if m.strip())
        blocklist = build_corpus_boilerplate_lines(
            first_mds,
            min_doc_coverage=_min_corpus_coverage(n_ok),
        )
        log.info("Corpus boilerplate candidate lines: %d (min_doc_coverage=%d)", len(blocklist), _min_corpus_coverage(n_ok))

    rows: list[dict[str, object]] = []
    for slug, url, main_path, ext_path, html_bytes, extract_meta in payloads:
        out_md = paths.planned_clean_path(slug)
        out_json = paths.normalize_sidecar_path(slug)
        extract_status = str(extract_meta.get("extract_status") or "unknown")

        if not html_bytes:
            rec = {
                "scheme": slug,
                "source_url": url,
                "normalize_status": "failed",
                "error": "missing_extracted_main_html",
                "extract_status": extract_status,
                "normalizer_version": NORMALIZER_VERSION,
                "language_note": "English-only v1 (per Phase 0).",
                "clean_md_path": str(out_md),
                "extracted_main_html_path": str(main_path),
            }
            rows.append(rec)
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(rec, indent=2), encoding="utf-8")
            continue

        out = normalize_extracted_html(html_bytes, corpus_line_blocklist=blocklist or None)
        norm_status = out.normalize_status
        if extract_status in ("empty_shell", "parse_error"):
            norm_status = "partial" if out.markdown.strip() else "empty"

        rec = {
            "scheme": slug,
            "source_url": url,
            "normalize_status": norm_status,
            "extract_status": extract_status,
            "normalizer_version": NORMALIZER_VERSION,
            "language_note": "English-only v1 (per Phase 0).",
            "char_count": out.char_count,
            "lines_removed_static": out.lines_removed_static,
            "lines_removed_corpus": out.lines_removed_corpus,
            "warnings": out.warnings,
            "clean_md_path": str(out_md),
            "extracted_main_html_path": str(main_path),
            "extract_sidecar_path": str(ext_path),
            "normalized_at_utc": datetime.now(timezone.utc).isoformat(),
        }
        out_md.parent.mkdir(parents=True, exist_ok=True)
        out_md.write_text(out.markdown, encoding="utf-8")
        out_json.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        rows.append(rec)
        log.info("%s -> %s (%d chars)", slug, norm_status, out.char_count)

    report_path = args.report or (paths.root / "normalize_report.json")
    bad = sum(1 for r in rows if r.get("normalize_status") in ("empty", "failed"))
    summary = {
        "phase": "2.4",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "normalizer_version": NORMALIZER_VERSION,
        "corpus_boilerplate_line_count": len(blocklist),
        "entry_count": len(rows),
        "bad_count": bad,
        "entries": rows,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Wrote normalize report: %s", report_path)
    print(json.dumps({"bad_count": bad, "total": len(rows), "report": str(report_path)}, indent=2))
    return 0 if bad <= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
