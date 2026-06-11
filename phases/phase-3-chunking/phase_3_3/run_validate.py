"""
Phase 3.3 — Validate chunk metadata, dedupe, and write index-build quality report.

Run from ``phases/phase-3-chunking``::

    python -m phase_3_3.run_validate
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from chunking.config_load import default_chunking_config_path
from phase_3_1.logging_setup import setup_phase3_logging
from phase_3_1.paths import Phase2ArtifactPaths, Phase3ArtifactPaths, load_workspace_config, phase3_chunking_package_root
from phase_3_1.registry_bridge import validate_registry_or_raise
from phase_3_3 import PHASE_3_3_VERSION
from phase_3_3.load_bundles import discover_chunk_bundles, load_chunk_bundle
from phase_3_3.paths import (
    phase3_index_build_quality_report_path,
    phase3_validated_manifest_path,
    validated_chunk_bundle_path,
)
from phase_3_3.pipeline import build_validated_bundle, process_bundle

log = logging.getLogger("phase3_chunking.phase_3_3.run")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3.3 — validate chunks for index build.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--scheme", type=str, default=None, help="Validate one scheme only.")
    parser.add_argument(
        "--allow-warnings",
        action="store_true",
        help="Exit 0 when only non-fatal issues (e.g. context limit flags, empty exclusions).",
    )
    args = parser.parse_args(argv)

    config = load_workspace_config(args.config)
    setup_phase3_logging(config)

    phase3_root = phase3_chunking_package_root()
    phase3_paths = Phase3ArtifactPaths.from_config(config, phase3_root)
    phase3_paths.ensure_dirs()
    phase2_paths = Phase2ArtifactPaths.from_config(config)

    registry = validate_registry_or_raise()
    url_by_scheme = {str(e["scheme"]): str(e["url"]) for e in registry["entries"]}

    if args.scheme:
        bundle_path = phase3_paths.chunks / f"{args.scheme.replace('/', '_')}.chunks.json"
        if not bundle_path.is_file():
            log.error("Missing chunk bundle: %s", bundle_path)
            return 2
        bundles = [load_chunk_bundle(bundle_path)]
    else:
        bundles = discover_chunk_bundles(phase3_paths)
        if not bundles:
            log.error("No chunk bundles in %s (run Phase 3.2 first)", phase3_paths.chunks)
            return 2

    log.info("Phase 3.3 validate — %d bundle(s)", len(bundles))

    results: list[dict] = []
    hard_fail_count = 0
    indexable_count = 0
    total_chunks_in = 0
    total_chunks_out = 0
    total_exact_dupes = 0
    total_context_exceeded = 0
    excluded_schemes: list[str] = []

    for bundle in bundles:
        registry_url = url_by_scheme.get(bundle.scheme, bundle.source_url)
        result = process_bundle(bundle, config, phase2_paths, registry_url)
        total_chunks_in += result.chunk_count_in
        total_chunks_out += result.chunk_count_out
        total_exact_dupes += result.dedupe_stats.get("exact_duplicates_removed", 0)
        total_context_exceeded += result.context_stats.get("chunks_exceeding_limit", 0)

        if result.hard_failures():
            hard_fail_count += 1
            for err in result.hard_failures():
                log.error("%s [%s] %s: %s", bundle.scheme, err.chunk_id, err.code, err.message)

        if result.indexable:
            indexable_count += 1
            validated = build_validated_bundle(bundle, result, config)
            out_path = validated_chunk_bundle_path(phase3_paths, bundle.scheme)
            out_path.write_text(json.dumps(validated, indent=2), encoding="utf-8")
            log.info("%s -> validated %d chunks", bundle.scheme, result.chunk_count_out)
        else:
            excluded_schemes.append(bundle.scheme)
            log.warning("%s excluded: %s", bundle.scheme, result.status)

        results.append(
            {
                "scheme": result.scheme,
                "source_url": result.source_url,
                "status": result.status,
                "indexable": result.indexable,
                "chunk_count_in": result.chunk_count_in,
                "chunk_count_out": result.chunk_count_out,
                "dedupe_stats": result.dedupe_stats,
                "context_limit_stats": result.context_stats,
                "errors": [
                    {"chunk_id": e.chunk_id, "code": e.code, "message": e.message}
                    for e in result.errors
                ],
                "validated_bundle_path": str(validated_chunk_bundle_path(phase3_paths, bundle.scheme))
                if result.indexable
                else None,
            },
        )

    generated_at = datetime.now(timezone.utc).isoformat()
    emb_model = str((config.get("embedding") or {}).get("model_id", ""))

    validated_manifest = {
        "phase": "3.3",
        "phase_3_3_version": PHASE_3_3_VERSION,
        "generated_at_utc": generated_at,
        "embedding_model_id": emb_model,
        "schemes_indexable": indexable_count,
        "schemes_total": len(results),
        "total_chunks_indexable": total_chunks_out,
        "entries": [r for r in results if r["indexable"]],
    }
    manifest_path = phase3_validated_manifest_path(phase3_paths)
    manifest_path.write_text(json.dumps(validated_manifest, indent=2), encoding="utf-8")

    quality_report = {
        "phase": "3.3",
        "phase_3_3_version": PHASE_3_3_VERSION,
        "generated_at_utc": generated_at,
        "embedding_model_id": emb_model,
        "embedding_max_input_tokens": int((config.get("embedding") or {}).get("max_input_tokens", 8192)),
        "summary": {
            "bundles_processed": len(results),
            "schemes_indexable": indexable_count,
            "schemes_excluded": len(excluded_schemes),
            "schemes_hard_failed": hard_fail_count,
            "total_chunks_in": total_chunks_in,
            "total_chunks_out": total_chunks_out,
            "exact_duplicates_removed": total_exact_dupes,
            "chunks_embedding_context_exceeded": total_context_exceeded,
            "ready_for_phase_3_4": hard_fail_count == 0 and indexable_count > 0,
        },
        "excluded_schemes": excluded_schemes,
        "per_scheme": results,
    }
    report_path = phase3_index_build_quality_report_path(phase3_paths)
    report_path.write_text(json.dumps(quality_report, indent=2), encoding="utf-8")

    log.info("Wrote %s", manifest_path)
    log.info("Wrote %s", report_path)
    log.info(
        "Phase 3.3 complete: indexable=%d/%d chunks_out=%d hard_fail_schemes=%d",
        indexable_count,
        len(results),
        total_chunks_out,
        hard_fail_count,
    )

    if hard_fail_count > 0:
        return 1
    if indexable_count == 0:
        return 1
    if total_context_exceeded > 0 and not args.allow_warnings:
        log.warning(
            "%d chunk(s) exceed embedding max_input_tokens (use --allow-warnings or fix in Phase 3.4)",
            total_context_exceeded,
        )
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
