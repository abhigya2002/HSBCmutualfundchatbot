"""
Phase 4.1 — Dry load: validate Phase 3 handoff and indexes (no query classification).

Run from ``phases/phase-4-retrieval``::

    python -m phase_4_1.dry_load
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from phase_4_1 import PHASE_4_1_VERSION
from phase_4_1.config_load import default_config_path, load_config, phase4_retrieval_root
from phase_4_1.handoff import build_index_handoff_context
from phase_4_1.index_loader import load_indexes
from phase_4_1.logging_setup import setup_logging
from phase_4_1.paths import Phase3Paths, RetrievalArtifactPaths

log = logging.getLogger("phase4_retrieval.phase_4_1.dry")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 4.1 dry load — index handoff validation.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--json-out", type=Path, default=None)
    parser.add_argument(
        "--skip-index-load",
        action="store_true",
        help="Validate paths only; do not import Phase 3 index classes.",
    )
    args = parser.parse_args(argv)

    config = load_config(args.config)
    setup_logging(config)

    root = phase4_retrieval_root()
    paths = RetrievalArtifactPaths.from_config(config, root)
    paths.ensure_dirs()
    phase3 = Phase3Paths.from_config(config)

    log.info("Phase 4.1 dry load — workspace: %s", root)
    log.info("Config: %s", args.config or default_config_path())

    ctx = build_index_handoff_context(config)
    load_issues = []

    if not args.skip_index_load and ctx.ready:
        loaded, load_issues = load_indexes(ctx, phase3.chunking_root, phase3.indexing_root)
        if loaded:
            log.info(
                "Indexes loaded: vector_dims=%s bm25_docs=%s records=%s",
                getattr(loaded.vector_index, "dimensions", "?"),
                getattr(loaded.keyword_index, "document_count", "?"),
                loaded.loaded_chunk_count,
            )
    elif args.skip_index_load:
        log.info("Skipped in-memory index load (--skip-index-load)")
    else:
        log.warning("Skipping index load due to handoff errors")

    all_issues = ctx.issues + load_issues
    errors = [i for i in all_issues if i.code.startswith("error_") or i.code.startswith("missing_")]
    warnings = [i for i in all_issues if i not in errors]

    manifest = {
        "phase": "4.1",
        "phase_4_1_version": PHASE_4_1_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_version": ctx.index_version,
        "embedding_model_id": ctx.embedding_model_id,
        "vector_index_dir": str(ctx.vector_index_dir),
        "keyword_index_dir": str(ctx.keyword_index_dir),
        "bm25_index_path": str(ctx.bm25_index_path),
        "chunk_records_path": str(ctx.chunk_records_path),
        "vector_chunk_count": ctx.vector_chunk_count,
        "keyword_chunk_count": ctx.keyword_chunk_count,
        "bm25_document_count": ctx.bm25_document_count,
        "registry_entry_count": ctx.registry_entry_count,
        "ready_for_phase_4_2": len(errors) == 0,
        "errors": [{"code": i.code, "message": i.message} for i in errors],
        "warnings": [{"code": i.code, "message": i.message} for i in warnings],
        "hybrid_merge_keys": (ctx.hybrid_contract.get("shared_merge_keys") or []),
    }

    out = args.json_out or paths.dry_manifest_path()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    paths.handoff_validation_path().write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote %s", out)

    for e in errors:
        log.error("[%s] %s", e.code, e.message)
    for w in warnings:
        log.warning("[%s] %s", w.code, w.message)

    if errors:
        return 1
    log.info("Dry load complete — ready for Phase 4.2.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
