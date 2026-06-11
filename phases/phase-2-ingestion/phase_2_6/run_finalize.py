"""
Phase 2.6 — Final ``clean_document`` JSON, corpus manifest, quality report, quarantine list.

Expects Phases 2.2–2.5 artifacts. Run from ``phases/phase-2-ingestion``::

    python -m phase_2_6.run_finalize
"""

from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from common.config import load_config, phase2_ingestion_root
from common.logging_setup import setup_ingestion_logging
from common.paths import ArtifactPaths
from common.registry_bridge import validate_registry_or_raise

from phase_2_6.clean_document import CLEAN_DOCUMENT_VERSION, build_clean_document_record
from phase_2_6.handoff import PHASE3_HANDOFF
from phase_2_6.quality import aggregate, parse_success

log = logging.getLogger("phase2_ingestion.phase_2_6")


def _read_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _quarantine_reasons(row: dict[str, object]) -> list[str]:
    reasons: list[str] = []
    if row.get("missing_clean_markdown"):
        reasons.append("missing_clean_markdown")
    ex = str(row.get("extract_status") or "")
    if ex in ("parse_error", "empty_shell"):
        reasons.append(f"extract_status={ex}")
    ns = row.get("normalize_status")
    if ns is not None and str(ns) in ("empty", "failed"):
        reasons.append(f"normalize_status={ns}")
    if row.get("doc_metadata_error") == "missing_clean_markdown":
        reasons.append("doc_metadata_missing_clean")
    if not parse_success(row) and not reasons:
        reasons.append("parse_success_criteria_not_met")
    return reasons


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 2.6 — clean_document + manifest + quality report.")
    parser.add_argument("--config", type=Path, default=None)
    args = parser.parse_args(argv)

    t_wall0 = time.perf_counter()
    phase2_root = phase2_ingestion_root()
    config = load_config(args.config)
    setup_ingestion_logging(config)
    paths = ArtifactPaths.from_config(config, phase2_root)
    paths.ensure_dirs()

    registry = validate_registry_or_raise()
    entries = sorted(registry["entries"], key=lambda e: int(e["id"]))

    manifest_rows: list[dict[str, object]] = []
    quality_rows: list[dict[str, object]] = []
    quarantine_slugs: list[str] = []

    for entry in entries:
        slug = str(entry["scheme"])
        url = str(entry["url"])
        clean_md = paths.planned_clean_path(slug)
        raw_html = paths.raw_html_path(slug)
        crawl = paths.crawl_meta_path(slug)
        extract_p = paths.extract_sidecar_path(slug)
        normalize_p = paths.normalize_sidecar_path(slug)
        meta_p = paths.planned_metadata_path(slug)
        clean_doc_p = paths.clean_document_path(slug)

        t0 = time.perf_counter()
        extract = _read_json(extract_p)
        normalize = _read_json(normalize_p)
        dm = _read_json(meta_p)

        raw_bytes = raw_html.stat().st_size if raw_html.exists() else 0
        clean_bytes = clean_md.stat().st_size if clean_md.exists() else 0

        row: dict[str, object] = {
            "scheme": slug,
            "source_url": url,
            "extract_status": extract.get("extract_status"),
            "normalize_status": normalize.get("normalize_status"),
            "missing_clean_markdown": not clean_md.exists(),
            "clean_md_bytes": clean_bytes,
            "raw_html_bytes": raw_bytes,
            "doc_metadata_error": dm.get("error"),
            "parse_success": parse_success(
                {
                    "extract_status": extract.get("extract_status"),
                    "normalize_status": normalize.get("normalize_status"),
                    "missing_clean_markdown": not clean_md.exists(),
                    "clean_md_bytes": clean_bytes,
                    "doc_metadata_error": dm.get("error"),
                }
            ),
        }
        row["assembly_ms"] = round((time.perf_counter() - t0) * 1000, 3)

        rec = build_clean_document_record(
            scheme=slug,
            source_url=url,
            clean_md_path=clean_md,
            doc_metadata_path=meta_p,
            raw_html_path=raw_html,
            crawl_path=crawl,
            extract_path=extract_p,
            normalize_path=normalize_p,
            clean_document_out=clean_doc_p,
        )
        clean_doc_p.parent.mkdir(parents=True, exist_ok=True)
        clean_doc_p.write_text(json.dumps(rec, indent=2), encoding="utf-8")

        reasons = _quarantine_reasons(row)
        quarantined = bool(reasons)
        if quarantined:
            quarantine_slugs.append(slug)
            qpath = paths.quarantine_review_path(slug)
            qpath.parent.mkdir(parents=True, exist_ok=True)
            qpath.write_text(
                json.dumps(
                    {
                        "scheme": slug,
                        "source_url": url,
                        "quarantined_at_utc": datetime.now(timezone.utc).isoformat(),
                        "reasons": reasons,
                        "artifact_paths": {
                            "raw_html": str(raw_html.resolve()),
                            "clean_markdown": str(clean_md.resolve()),
                            "extract_sidecar": str(extract_p.resolve()),
                            "normalize_sidecar": str(normalize_p.resolve()),
                            "doc_metadata": str(meta_p.resolve()),
                            "clean_document": str(clean_doc_p.resolve()),
                        },
                    },
                    indent=2,
                ),
                encoding="utf-8",
            )
            log.warning("Quarantined for review: %s (%s)", slug, "; ".join(reasons))
        else:
            log.info("OK: %s", slug)

        manifest_rows.append(
            {
                "scheme": slug,
                "source_url": url,
                "parse_success": row["parse_success"],
                "quarantined": quarantined,
                "paths": {
                    "raw_html": str(raw_html.resolve()),
                    "clean_markdown": str(clean_md.resolve()),
                    "clean_document": str(clean_doc_p.resolve()),
                    "doc_metadata": str(meta_p.resolve()),
                },
            }
        )
        quality_rows.append(row)

    wall_ms = round((time.perf_counter() - t_wall0) * 1000, 2)
    agg = aggregate(quality_rows)

    manifest = {
        "manifest_version": CLEAN_DOCUMENT_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "entry_count": len(manifest_rows),
        "entries": manifest_rows,
    }
    mpath = paths.phase2_corpus_manifest_path()
    mpath.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote corpus manifest: %s", mpath)

    qreport = {
        "phase": "2.6",
        "clean_document_version": CLEAN_DOCUMENT_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "wall_time_ms_total": wall_ms,
        "aggregate": agg,
        "quarantine_slugs": quarantine_slugs,
        "entries": quality_rows,
        "phase3_handoff": PHASE3_HANDOFF,
    }
    report_path = paths.phase2_quality_report_path()
    report_path.write_text(json.dumps(qreport, indent=2), encoding="utf-8")
    log.info("Wrote quality report: %s", report_path)

    n = len(quality_rows) or 1
    failures = n - int(agg["parse_success_count"])
    print(
        json.dumps(
            {
                "parse_success_rate": agg["parse_success_rate"],
                "parse_success_count": agg["parse_success_count"],
                "total": n,
                "quarantine_count": len(quarantine_slugs),
                "manifest": str(mpath),
                "quality_report": str(report_path),
            },
            indent=2,
        )
    )
    # Same gate as Phase 2.3 extract: allow at most one failure in 16-URL corpus (~94% floor).
    return 0 if failures <= 1 else 1


if __name__ == "__main__":
    raise SystemExit(main())
