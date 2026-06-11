"""
Phase 2.5 — Build per-scheme ``doc_metadata`` JSON under ``artifacts/metadata/``.

Requires Phase 2.4 clean Markdown (and benefits from 2.2 crawl + 2.3/2.4 sidecars).

Run from ``phases/phase-2-ingestion``::

    python -m phase_2_5.run_metadata
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

from phase_2_5.doc_metadata import METADATA_BUILDER_VERSION, build_doc_metadata

log = logging.getLogger("phase2_ingestion.phase_2_5")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2.5 — doc_metadata + candidate tags.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--report", type=Path, default=None)
    args = parser.parse_args(argv)

    phase2_root = phase2_ingestion_root()
    config = load_config(args.config)
    setup_ingestion_logging(config)
    paths = ArtifactPaths.from_config(config, phase2_root)
    paths.ensure_dirs()

    registry = validate_registry_or_raise()
    entries = sorted(registry["entries"], key=lambda e: int(e["id"]))

    rows: list[dict[str, object]] = []
    for entry in entries:
        slug = str(entry["scheme"])
        url = str(entry["url"])
        clean_path = paths.planned_clean_path(slug)
        raw_path = paths.raw_html_path(slug)
        crawl_path = paths.crawl_meta_path(slug)
        extract_path = paths.extract_sidecar_path(slug)
        normalize_path = paths.normalize_sidecar_path(slug)
        meta_path = paths.planned_metadata_path(slug)

        rec = build_doc_metadata(
            scheme=slug,
            source_url=url,
            clean_md_path=clean_path,
            raw_html_path=raw_path,
            crawl_path=crawl_path,
            extract_path=extract_path,
            normalize_path=normalize_path,
            metadata_out_path=meta_path,
            registry_entry=entry,
        )
        rows.append(rec)
        miss = rec.get("error") or (
            "ok"
            if rec.get("content_sha256")
            else "incomplete"
        )
        log.info("%s doc_metadata -> %s", slug, miss)

    report_path = args.report or (paths.root / "doc_metadata_report.json")
    bad = sum(1 for r in rows if r.get("error") == "missing_clean_markdown")
    summary = {
        "phase": "2.5",
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "metadata_builder_version": METADATA_BUILDER_VERSION,
        "entry_count": len(rows),
        "missing_clean_count": bad,
        "entries": rows,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Wrote doc_metadata report: %s", report_path)
    print(json.dumps({"missing_clean_count": bad, "total": len(rows), "report": str(report_path)}, indent=2))
    return 0 if bad <= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
