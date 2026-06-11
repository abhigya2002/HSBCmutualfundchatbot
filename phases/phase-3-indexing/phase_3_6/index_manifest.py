"""Rollup index manifest across Phase 3.2–3.5."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from phase_3_6 import PHASE_3_6_VERSION


def build_index_manifest(
    *,
    index_version: str,
    chunking_artifacts: Path,
    indexing_artifacts: Path,
    partial_corpus: bool,
    schemes_indexable: int,
    benchmark_report: Mapping[str, Any],
    config_snapshot_path: Path,
    pipeline_steps: list[dict[str, Any]],
) -> dict[str, Any]:
    vector_active = json.loads(
        (chunking_artifacts / "indexes" / "vector" / "active.json").read_text(encoding="utf-8"),
    )
    keyword_active = json.loads(
        (indexing_artifacts / "indexes" / "keyword" / "active.json").read_text(encoding="utf-8"),
    )
    return {
        "phase": "3.6",
        "phase_3_6_version": PHASE_3_6_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_version": index_version,
        "partial_corpus": partial_corpus,
        "schemes_expected": 16,
        "schemes_indexable": schemes_indexable,
        "total_chunks": vector_active.get("chunk_count"),
        "embedding_model_id": vector_active.get("embedding_model_id"),
        "vector_index_dir": vector_active.get("vector_index_dir"),
        "keyword_index_dir": keyword_active.get("keyword_index_dir"),
        "config_snapshot": str(config_snapshot_path),
        "pipeline_steps": pipeline_steps,
        "benchmark_passed": benchmark_report.get("passed"),
        "recall_at_k": benchmark_report.get("recall_at_k"),
        "ready_for_phase_4": bool(benchmark_report.get("passed")) and not partial_corpus,
    }
