"""
Phase 2.3 — Extract main content from each raw HTML snapshot.

Requires Phase 2.2 outputs under ``artifacts/raw/*.html``.

Run from ``phases/phase-2-ingestion``::

    python -m phase_2_3.run_extract
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from common.config import load_config, phase2_ingestion_root
from common.logging_setup import setup_ingestion_logging
from common.paths import ArtifactPaths
from common.registry_bridge import validate_registry_or_raise

from phase_2_3.extract import EXTRACT_VERSION, extract_main_fragment

log = logging.getLogger("phase2_ingestion.phase_2_3")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2.3 — extract main HTML from raw snapshots.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    phase2_root = phase2_ingestion_root()
    config = load_config(args.config)
    setup_ingestion_logging(config)
    paths = ArtifactPaths.from_config(config, phase2_root)
    paths.ensure_dirs()

    registry = validate_registry_or_raise()
    rows: list[dict[str, object]] = []

    for entry in sorted(registry["entries"], key=lambda e: int(e["id"])):
        slug = str(entry["scheme"])
        url = str(entry["url"])
        raw_path = paths.raw_html_path(slug)
        crawl_path = paths.crawl_meta_path(slug)
        out_html = paths.extracted_main_html_path(slug)
        out_json = paths.extract_sidecar_path(slug)

        fetch_status: str | None = None
        if crawl_path.exists():
            try:
                fetch_status = str(json.loads(crawl_path.read_text(encoding="utf-8")).get("fetch_status"))
            except Exception:
                fetch_status = "crawl_read_error"

        if not raw_path.exists():
            log.error("Missing raw HTML for %s (%s)", slug, raw_path)
            rec = {
                "scheme": slug,
                "source_url": url,
                "extract_status": "parse_error",
                "error": "missing_raw_html",
                "fetch_status": fetch_status,
                "parser_version": EXTRACT_VERSION,
            }
            rows.append(rec)
            out_json.parent.mkdir(parents=True, exist_ok=True)
            out_json.write_text(json.dumps(rec, indent=2), encoding="utf-8")
            continue

        html_bytes = raw_path.read_bytes()
        out = extract_main_fragment(html_bytes)
        rec = {
            "scheme": slug,
            "source_url": url,
            "extract_status": out.extract_status,
            "text_length": out.text_length,
            "selector_used": out.selector_used,
            "parser_version": EXTRACT_VERSION,
            "extracted_at_utc": datetime.now(timezone.utc).isoformat(),
            "fetch_status": fetch_status,
            "raw_html_path": str(raw_path),
            "main_html_path": str(out_html),
            "sidecar_path": str(out_json),
            "error": out.error,
        }
        out_html.parent.mkdir(parents=True, exist_ok=True)
        out_html.write_text(out.main_html, encoding="utf-8")
        out_json.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        rows.append(rec)
        log.info("%s -> %s (%d chars)", slug, out.extract_status, out.text_length)

    report_path = args.report or (paths.root / "extract_report.json")
    bad = sum(1 for r in rows if r.get("extract_status") in ("empty_shell", "parse_error"))
    summary = {
        "phase": "2.3",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "entry_count": len(rows),
        "bad_count": bad,
        "entries": rows,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Wrote extract report: %s", report_path)
    print(json.dumps({"bad_count": bad, "total": len(rows), "report": str(report_path)}, indent=2))
    # Allow at most one failure for 16-URL corpus (~94%) per architecture >=95% target margin
    return 0 if bad <= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
