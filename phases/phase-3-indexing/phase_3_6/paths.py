"""Phase 3.6 artifact paths."""

from __future__ import annotations

from pathlib import Path

from phase_3_5.config_load import phase3_indexing_root
from phase_3_5.paths import IndexingArtifactPaths


def default_benchmark_path() -> Path:
    return phase3_indexing_root() / "benchmarks" / "retrieval_benchmark.json"


def phase3_index_manifest_path(paths: IndexingArtifactPaths) -> Path:
    return paths.root / "phase3_index_manifest.json"


def phase3_benchmark_report_path(paths: IndexingArtifactPaths) -> Path:
    return paths.root / "phase3_retrieval_benchmark_report.json"


def phase4_handoff_path(paths: IndexingArtifactPaths) -> Path:
    return paths.root / "phase4_retrieval_handoff.json"
