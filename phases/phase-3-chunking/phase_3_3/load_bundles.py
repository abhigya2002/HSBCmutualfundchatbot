"""Load Phase 3.2 chunk bundles from disk."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase_3_1.paths import Phase3ArtifactPaths
from phase_3_2.paths import chunk_bundle_path


@dataclass(frozen=True)
class ChunkBundle:
    scheme: str
    source_url: str
    path: Path
    raw: dict[str, Any]

    @property
    def chunks(self) -> list[dict[str, Any]]:
        items = self.raw.get("chunks")
        return list(items) if isinstance(items, list) else []


def load_chunk_bundle(path: Path) -> ChunkBundle:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected object in {path}")
    scheme = str(data.get("scheme") or path.stem.replace(".chunks", ""))
    source_url = str(data.get("source_url") or "")
    return ChunkBundle(scheme=scheme, source_url=source_url, path=path, raw=data)


def discover_chunk_bundles(phase3: Phase3ArtifactPaths) -> list[ChunkBundle]:
    bundles: list[ChunkBundle] = []
    if not phase3.chunks.is_dir():
        return bundles
    for path in sorted(phase3.chunks.glob("*.chunks.json")):
        bundles.append(load_chunk_bundle(path))
    return bundles


def bundle_path_for_scheme(phase3: Phase3ArtifactPaths, scheme: str) -> Path:
    return chunk_bundle_path(phase3, scheme)
