"""Phase 3.2 chunk artifact paths."""

from __future__ import annotations

from pathlib import Path

from phase_3_1.paths import Phase3ArtifactPaths


def chunk_bundle_path(phase3: Phase3ArtifactPaths, scheme_slug: str) -> Path:
    """Per-scheme chunk bundle JSON (``{slug}.chunks.json``)."""
    slug = scheme_slug.replace("/", "_")
    return phase3.chunks / f"{slug}.chunks.json"


def phase3_chunk_manifest_path(phase3: Phase3ArtifactPaths) -> Path:
    return phase3.root / "phase3_chunk_manifest.json"
