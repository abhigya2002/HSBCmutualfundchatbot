"""
Phase 3.5 — Build BM25 keyword index for hybrid retrieval.

Run from ``phases/phase-3-indexing``::

    python -m phase_3_5.run_keyword_index
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from datetime import datetime, timezone
from pathlib import Path

from phase_3_5 import PHASE_3_5_VERSION
from phase_3_5.config_load import default_config_path, load_config, phase3_indexing_root
from phase_3_5.index_build import activate_keyword_index, build_keyword_index
from phase_3_5.paths import IndexingArtifactPaths

log = logging.getLogger("phase3_indexing.phase_3_5.run")


def _setup_logging(config: dict) -> None:
    log_cfg = config.get("logging") or {}
    level = getattr(logging, str(log_cfg.get("level", "INFO")).upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3.5 — BM25 keyword index build.")
    parser.add_argument("--config", type=Path, default=None)
    parser.add_argument("--index-version", type=str, default=None, help="Align with vector index version.")
    parser.add_argument("--no-activate", action="store_true")
    args = parser.parse_args(argv)

    config = load_config(args.config)
    _setup_logging(config)

    indexing_root = phase3_indexing_root()
    paths = IndexingArtifactPaths.from_config(config, indexing_root)
    paths.ensure_dirs()

    log.info("Phase 3.5 keyword index build")

    try:
        result = build_keyword_index(config, paths, index_version=args.index_version)
    except Exception:
        log.exception("Keyword index build failed")
        return 1

    if not args.no_activate:
        active = activate_keyword_index(paths, result, config)
        log.info("Activated keyword index: %s", active)

    report = {
        "phase": "3.5",
        "phase_3_5_version": PHASE_3_5_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_version": result.index_version,
        "chunk_count": result.chunk_count,
        "term_count": result.term_count,
        "keyword_index_dir": str(result.keyword_index_dir),
        "hybrid_contract": str(paths.hybrid_contract_path()),
        "ready_for_phase_4": True,
    }
    paths.keyword_build_report().write_text(json.dumps(report, indent=2), encoding="utf-8")
    log.info("Wrote %s", paths.keyword_build_report())
    log.info(
        "Phase 3.5 complete: %d docs, %d terms, version=%s",
        result.chunk_count,
        result.term_count,
        result.index_version,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
