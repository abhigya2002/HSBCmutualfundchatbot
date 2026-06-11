"""
Phase 3.2 — Build and persist chunk artifacts for all indexable schemes.

Run from ``phases/phase-3-chunking``::

    python -m phase_3_2.run_chunk
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from chunking.config_load import default_chunking_config_path
from chunking.contracts import CHUNK_STRATEGY_VERSION, ChunkingParams
from phase_3_1.handoff import validate_all_schemes
from phase_3_1.logging_setup import setup_phase3_logging
from phase_3_1.paths import Phase2ArtifactPaths, Phase3ArtifactPaths, load_workspace_config, phase3_chunking_package_root
from phase_3_1.registry_bridge import validate_registry_or_raise
from phase_3_2 import PHASE_3_2_VERSION
from phase_3_2.chunk_scheme import chunk_scheme
from phase_3_2.load import load_scheme_chunk_input
from phase_3_2.paths import chunk_bundle_path, phase3_chunk_manifest_path
from phase_3_2.persist import build_chunk_bundle, write_chunk_bundle

log = logging.getLogger("phase3_chunking.phase_3_2.run")


def _config_snapshot(config: dict) -> dict:
    return {
        "default_strategy": config.get("default_strategy"),
        "chars_per_token_estimate": config.get("chars_per_token_estimate"),
        "target_tokens_min": config.get("target_tokens_min"),
        "target_tokens_max": config.get("target_tokens_max"),
        "overlap_tokens_min": config.get("overlap_tokens_min"),
        "overlap_tokens_max": config.get("overlap_tokens_max"),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3.2 — chunk corpus and persist artifacts.")
    parser.add_argument("--config", type=Path, default=None, help="Chunking JSON config path.")
    parser.add_argument("--scheme", type=str, default=None, help="Chunk a single scheme slug only.")
    parser.add_argument(
        "--skip-handoff",
        action="store_true",
        help="Skip Phase 3.1 handoff gate (not recommended).",
    )
    parser.add_argument(
        "--strict-sha256",
        action="store_true",
        help="Fail when Markdown bytes differ from Phase 2.6 body_sha256 metadata.",
    )
    args = parser.parse_args(argv)

    config = load_workspace_config(args.config)
    setup_phase3_logging(config)

    phase3_root = phase3_chunking_package_root()
    phase3_paths = Phase3ArtifactPaths.from_config(config, phase3_root)
    phase3_paths.ensure_dirs()
    phase2_paths = Phase2ArtifactPaths.from_config(config)

    registry = validate_registry_or_raise()
    entries = registry["entries"]
    params = ChunkingParams.from_mapping(config)
    strategy = str(config.get("default_strategy", "section_sliding_v1"))
    snapshot = _config_snapshot(config)

    log.info("Phase 3.2 chunk run — strategy=%s workspace=%s", strategy, phase3_paths.chunks)

    handoff_results = validate_all_schemes(entries, phase2_paths, config)
    indexable = {r.scheme for r in handoff_results if r.indexable}
    blocked = {r.scheme: r.blockers for r in handoff_results if not r.indexable}

    if args.scheme:
        entries = [e for e in entries if str(e["scheme"]) == args.scheme]
        if not entries:
            log.error("Unknown scheme: %s", args.scheme)
            return 2

    manifest_rows: list[dict] = []
    errors: list[str] = []
    total_chunks = 0

    for e in sorted(entries, key=lambda x: int(x["id"])):
        scheme = str(e["scheme"])
        url = str(e["url"])

        if scheme in blocked and not args.skip_handoff:
            log.warning("Skipping %s (handoff blocked): %s", scheme, blocked[scheme])
            manifest_rows.append(
                {
                    "scheme": scheme,
                    "source_url": url,
                    "status": "skipped_handoff",
                    "blockers": blocked[scheme],
                    "chunk_count": 0,
                },
            )
            continue

        if not args.skip_handoff and scheme not in indexable:
            manifest_rows.append(
                {
                    "scheme": scheme,
                    "source_url": url,
                    "status": "skipped_handoff",
                    "blockers": blocked.get(scheme, ["not_indexable"]),
                    "chunk_count": 0,
                },
            )
            continue

        try:
            inp = load_scheme_chunk_input(scheme, url, phase2_paths, strict_sha256=args.strict_sha256)
            if inp.sha256_mismatch:
                log.warning(
                    "%s: body_sha256 mismatch (using current Markdown; re-run Phase 2.6 to refresh metadata)",
                    scheme,
                )
            chunks = chunk_scheme(inp, config, params)
            if not chunks and inp.body.strip():
                raise RuntimeError("chunker produced zero chunks for non-empty body")

            bundle = build_chunk_bundle(
                inp,
                chunks,
                strategy=strategy,
                chunking_config_snapshot=snapshot,
            )
            out_path = chunk_bundle_path(phase3_paths, scheme)
            write_chunk_bundle(out_path, bundle)
            total_chunks += len(chunks)
            log.info("%s -> %d chunks (%s)", scheme, len(chunks), out_path.name)
            manifest_rows.append(
                {
                    "scheme": scheme,
                    "source_url": inp.source_url,
                    "status": "ok",
                    "chunk_count": len(chunks),
                    "chunk_bundle_path": str(out_path),
                    "body_sha256": inp.body_sha256,
                    "sha256_mismatch": inp.sha256_mismatch,
                },
            )
        except Exception as exc:
            log.exception("Failed to chunk %s", scheme)
            errors.append(f"{scheme}: {exc}")
            manifest_rows.append(
                {
                    "scheme": scheme,
                    "source_url": url,
                    "status": "error",
                    "error": str(exc),
                    "chunk_count": 0,
                },
            )

    ok_count = sum(1 for r in manifest_rows if r.get("status") == "ok")
    manifest = {
        "phase": "3.2",
        "phase_3_2_version": PHASE_3_2_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "default_strategy": strategy,
        "chunk_strategy_version": CHUNK_STRATEGY_VERSION,
        "schemes_ok": ok_count,
        "schemes_total": len(manifest_rows),
        "total_chunks": total_chunks,
        "entries": manifest_rows,
    }

    manifest_path = phase3_chunk_manifest_path(phase3_paths)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote manifest to %s", manifest_path)

    log.info(
        "Phase 3.2 complete: %d/%d schemes chunked, %d total chunks.",
        ok_count,
        len(manifest_rows),
        total_chunks,
    )

    if errors:
        return 1
    if ok_count == 0:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
