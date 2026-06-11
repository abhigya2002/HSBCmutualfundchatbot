"""
Phase 3.4 — Embed validated chunks and build versioned vector index.

Run from ``phases/phase-3-chunking``::

    python -m phase_3_4.run_embed
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
from phase_3_1.paths import Phase3ArtifactPaths, load_workspace_config, phase3_chunking_package_root
from phase_3_4 import PHASE_3_4_VERSION
from phase_3_4.index_build import activate_index, build_vector_index
from phase_3_4.paths import vector_active_pointer_path

log = logging.getLogger("phase3_chunking.phase_3_4.run")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3.4 — embeddings + vector index build.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument(
        "--index-version",
        type=str,
        default=None,
        help="Explicit index version id (default: auto-generated).",
    )
    parser.add_argument(
        "--no-activate",
        action="store_true",
        help="Build index but do not update indexes/vector/active.json.",
    )
    args = parser.parse_args(argv)

    config = load_workspace_config(args.config)
    setup_phase3_logging(config)

    phase3_root = phase3_chunking_package_root()
    phase3_paths = Phase3ArtifactPaths.from_config(config, phase3_root)
    phase3_paths.ensure_dirs()
    (phase3_paths.indexes / "vector").mkdir(parents=True, exist_ok=True)

    emb_cfg = config.get("embedding") or {}
    log.info(
        "Phase 3.4 embed — provider=%s model=%s",
        emb_cfg.get("provider", "hash_v1"),
        emb_cfg.get("model_id"),
    )

    try:
        result = build_vector_index(
            phase3_paths,
            config,
            index_version=args.index_version,
        )
    except Exception as exc:
        log.exception("Index build failed")
        return 1

    if not args.no_activate:
        active_path = activate_index(phase3_paths, result)
        log.info("Activated vector index: %s", active_path)
    else:
        active_path = vector_active_pointer_path(phase3_paths)

    summary_path = phase3_paths.root / "phase3_embedding_build_report.json"
    summary = {
        "phase": "3.4",
        "phase_3_4_version": PHASE_3_4_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_version": result.index_version,
        "embedding_model_id": result.embedding_model_id,
        "provider": result.provider,
        "dimensions": result.dimensions,
        "chunk_count": result.chunk_count,
        "embeddings_dir": str(result.embeddings_dir),
        "vector_index_dir": str(result.index_dir),
        "active_pointer": str(active_path) if not args.no_activate else None,
        "ready_for_phase_3_5": True,
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    log.info("Wrote %s", summary_path)

    log.info(
        "Phase 3.4 complete: %d chunks, index_version=%s, model=%s",
        result.chunk_count,
        result.index_version,
        result.embedding_model_id,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
