"""Phase 3.3 validated chunk artifact paths."""

from __future__ import annotations

from pathlib import Path

from phase_3_1.paths import Phase3ArtifactPaths
from phase_3_2.paths import chunk_bundle_path, phase3_chunk_manifest_path


def validated_chunk_bundle_path(phase3: Phase3ArtifactPaths, scheme_slug: str) -> Path:
    slug = scheme_slug.replace("/", "_")
    return phase3.chunks_validated / f"{slug}.chunks.json"


def phase3_validated_manifest_path(phase3: Phase3ArtifactPaths) -> Path:
    return phase3.root / "phase3_validated_manifest.json"


def phase3_index_build_quality_report_path(phase3: Phase3ArtifactPaths) -> Path:
    return phase3.root / "phase3_index_build_quality_report.json"


__all__ = [
    "chunk_bundle_path",
    "phase3_chunk_manifest_path",
    "validated_chunk_bundle_path",
    "phase3_validated_manifest_path",
    "phase3_index_build_quality_report_path",
]
