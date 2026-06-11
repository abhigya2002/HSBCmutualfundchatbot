"""
Phase 3.1 — Dry pipeline: workspace dirs, config, Phase 2 handoff validation (no chunk/embed).

Run from ``phases/phase-3-chunking``::

    python -m phase_3_1.dry_enumerate
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from chunking.config_load import default_chunking_config_path
from chunking.contracts import ChunkingParams
from phase_3_1 import PHASE_3_1_VERSION
from phase_3_1.handoff import validate_all_schemes
from phase_3_1.logging_setup import setup_phase3_logging
from phase_3_1.paths import (
    Phase2ArtifactPaths,
    Phase3ArtifactPaths,
    load_workspace_config,
    phase3_chunking_package_root,
)
from phase_3_1.registry_bridge import validate_registry_or_raise

log = logging.getLogger("phase3_chunking.phase_3_1.dry")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Phase 3.1 dry enumeration: workspace + Phase 2 handoff (no embedding).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        help=f"Path to JSON config (default: {default_chunking_config_path()})",
    )
    parser.add_argument(
        "--json-out",
        type=Path,
        default=None,
        help="Write handoff manifest JSON (default: artifacts/phase3_1_dry_manifest.json).",
    )
    parser.add_argument(
        "--allow-blockers",
        action="store_true",
        help="Exit 0 even when some schemes are not indexable (still report blockers).",
    )
    args = parser.parse_args(argv)

    phase3_root = phase3_chunking_package_root()
    config = load_workspace_config(args.config)
    setup_phase3_logging(config)

    log.info("Phase 3.1 dry run — workspace: %s", phase3_root)
    log.info("Loading config from %s", args.config or default_chunking_config_path())

    phase3_paths = Phase3ArtifactPaths.from_config(config, phase3_root)
    phase3_paths.ensure_dirs()
    log.info(
        "Phase 3 artifact dirs ready: chunks=%s embeddings=%s indexes=%s logs=%s",
        phase3_paths.chunks,
        phase3_paths.embeddings,
        phase3_paths.indexes,
        phase3_paths.logs,
    )

    phase2_paths = Phase2ArtifactPaths.from_config(config)
    log.info("Phase 2 artifact root: %s", phase2_paths.root)
    if not phase2_paths.root.is_dir():
        log.error("Phase 2 artifact root does not exist: %s", phase2_paths.root)
        return 2

    params = ChunkingParams.from_mapping(config)
    strategy = str(config.get("default_strategy", "section_sliding_v1"))
    log.info(
        "Chunking params: strategy=%s tokens=%s-%s overlap=%s-%s chars_per_token=%s",
        strategy,
        params.target_tokens_min,
        params.target_tokens_max,
        params.overlap_tokens_min,
        params.overlap_tokens_max,
        params.chars_per_token,
    )

    registry = validate_registry_or_raise()
    entries = registry["entries"]
    log.info("Registry validated: %d entries", len(entries))

    results = validate_all_schemes(entries, phase2_paths, config)
    indexable_count = sum(1 for r in results if r.indexable)

    for r in results:
        status = "OK" if r.indexable else "BLOCKED"
        blockers = ",".join(r.blockers) if r.blockers else "-"
        print(f"{status:7}  {r.scheme:50}  {blockers}")

    manifest = {
        "phase": "3.1",
        "phase_3_1_version": PHASE_3_1_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "phase3_artifact_root": str(phase3_paths.root),
        "phase2_artifact_root": str(phase2_paths.root),
        "default_strategy": strategy,
        "chunking_params": {
            "chars_per_token_estimate": params.chars_per_token,
            "target_tokens_min": params.target_tokens_min,
            "target_tokens_max": params.target_tokens_max,
            "overlap_tokens_min": params.overlap_tokens_min,
            "overlap_tokens_max": params.overlap_tokens_max,
        },
        "entry_count": len(results),
        "indexable_count": indexable_count,
        "blocked_count": len(results) - indexable_count,
        "entries": [r.to_dict() for r in results],
    }

    out_path = args.json_out or phase3_paths.dry_manifest_path()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote manifest to %s", out_path)

    handoff_path = phase3_paths.handoff_report_path()
    handoff_path.write_text(
        json.dumps(
            {
                "phase": "3.1",
                "summary": {
                    "indexable_count": indexable_count,
                    "blocked_count": len(results) - indexable_count,
                    "ready_for_phase_3_2": indexable_count == len(results),
                },
                "entries": [r.to_dict() for r in results],
            },
            indent=2,
        ),
        encoding="utf-8",
    )
    log.info("Wrote handoff report to %s", handoff_path)

    log.info(
        "Dry enumeration complete: %d/%d schemes indexable.",
        indexable_count,
        len(results),
    )

    if indexable_count < len(results) and not args.allow_blockers:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
