"""
Phase 3.6 — One-command index pipeline (3.2 → 3.5) + benchmark evaluation.

Run from ``phases/phase-3-indexing``::

    python -m phase_3_6.run_build_all
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from pathlib import Path

from phase_3_5.config_load import load_config as load_indexing_config, phase3_indexing_root
from phase_3_5.paths import IndexingArtifactPaths
from phase_3_6 import PHASE_3_6_VERSION
from phase_3_6.benchmarks import load_benchmark
from phase_3_6.evaluate import run_benchmark_evaluation
from phase_3_6.handoff import build_phase4_handoff
from phase_3_6.hybrid_search import _chunking_root
from phase_3_6.index_manifest import build_index_manifest
from phase_3_6.orchestrate import run_full_index_pipeline, write_config_snapshot
from phase_3_6.paths import (
    phase3_benchmark_report_path,
    phase3_index_manifest_path,
    phase4_handoff_path,
)
from phase_3_6.versioning import build_corpus_index_version

log = logging.getLogger("phase3_indexing.phase_3_6.run")


def _setup_logging(config: dict) -> None:
    level = getattr(logging, str((config.get("logging") or {}).get("level", "INFO")).upper(), logging.INFO)
    logging.basicConfig(level=level, format="%(asctime)s %(levelname)s [%(name)s] %(message)s")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Phase 3.6 — full index build + benchmark.")
    parser.add_argument("--indexing-config", type=Path, default=None)
    parser.add_argument("--chunking-config", type=Path, default=None)
    parser.add_argument("--index-version", type=str, default=None)
    parser.add_argument("--eval-only", action="store_true", help="Skip pipeline; evaluate active indexes.")
    parser.add_argument("--allow-partial", action="store_true", help="Allow partial corpus (<16 schemes).")
    parser.add_argument(
        "--skip-pipeline",
        action="store_true",
        help="Alias for --eval-only.",
    )
    args = parser.parse_args(argv)

    indexing_root = phase3_indexing_root()
    indexing_config = load_indexing_config(args.indexing_config)
    _setup_logging(indexing_config)

    chunking_root = _chunking_root(indexing_root)
    chunking_config_path = args.chunking_config or (chunking_root / "config" / "chunking.defaults.json")
    chunking_config = json.loads(chunking_config_path.read_text(encoding="utf-8"))

    paths = IndexingArtifactPaths.from_config(indexing_config, indexing_root)
    paths.ensure_dirs()

    index_version = build_corpus_index_version(chunking_config, indexing_config, explicit=args.index_version)
    log.info("Phase 3.6 — index_version=%s", index_version)

    partial = False
    schemes_indexable = 16
    step_rows: list[dict] = []

    if not args.eval_only and not args.skip_pipeline:
        pipeline = run_full_index_pipeline(
            chunking_root=chunking_root,
            indexing_root=indexing_root,
            chunking_config_path=chunking_config_path,
            index_version=index_version,
        )
        step_rows = [{"name": s.name, "exit_code": s.exit_code} for s in pipeline.steps]
        partial = pipeline.partial_corpus
        schemes_indexable = pipeline.schemes_indexable or 0
        if not pipeline.success:
            log.error("Pipeline step failed")
            return 1
        if partial and not args.allow_partial:
            log.error(
                "Partial corpus: %d/16 schemes indexable (use --allow-partial to continue)",
                schemes_indexable,
            )
            return 1
    else:
        log.info("Skipping pipeline (--eval-only)")
        report_path = chunking_root / "artifacts" / "phase3_index_build_quality_report.json"
        if report_path.is_file():
            data = json.loads(report_path.read_text(encoding="utf-8"))
            per = data.get("per_scheme") or []
            schemes_indexable = sum(1 for r in per if r.get("indexable"))
            partial = schemes_indexable < 16
        active = chunking_root / "artifacts" / "indexes" / "vector" / "active.json"
        if active.is_file() and not args.index_version:
            index_version = str(json.loads(active.read_text(encoding="utf-8"))["index_version"])

    snapshot_path = write_config_snapshot(
        paths.root, index_version, chunking_config, indexing_config,
    )

    log.info("Running retrieval benchmark (%d queries)", len(load_benchmark()))
    bench = run_benchmark_evaluation(indexing_root, indexing_config)
    bench_path = phase3_benchmark_report_path(paths)
    bench_payload = {
        "phase": "3.6",
        "phase_3_6_version": PHASE_3_6_VERSION,
        "index_version": index_version,
        **bench.to_dict(),
    }
    bench_path.write_text(json.dumps(bench_payload, indent=2), encoding="utf-8")
    log.info("Wrote %s (recall@%d=%.2f, passed=%s)", bench_path, bench.k, bench.recall_at_k, bench.passed)

    manifest = build_index_manifest(
        index_version=index_version,
        chunking_artifacts=chunking_root / "artifacts",
        indexing_artifacts=paths.root,
        partial_corpus=partial,
        schemes_indexable=schemes_indexable,
        benchmark_report=bench_payload,
        config_snapshot_path=snapshot_path,
        pipeline_steps=step_rows,
    )
    manifest_path = phase3_index_manifest_path(paths)
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    log.info("Wrote %s", manifest_path)

    handoff = build_phase4_handoff(
        index_version=index_version,
        chunking_root=chunking_root,
        indexing_root=indexing_root,
        index_manifest=manifest,
        benchmark_report=bench_payload,
        hybrid_contract_path=paths.hybrid_contract_path(),
    )
    handoff_path = phase4_handoff_path(paths)
    handoff_path.write_text(json.dumps(handoff, indent=2), encoding="utf-8")
    log.info("Wrote %s", handoff_path)

    if not bench.passed:
        log.error("Benchmark below threshold %.2f", bench.threshold)
        return 1
    if partial and not args.allow_partial:
        return 1
    log.info("Phase 3.6 complete — ready_for_phase_4=%s", manifest.get("ready_for_phase_4"))
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
