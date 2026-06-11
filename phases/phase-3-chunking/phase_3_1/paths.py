"""Phase 3 artifact layout (chunks, embeddings, indexes, logs) and Phase 2 path resolution."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from chunking.config_load import resolve_phase2_artifact_root


def phase3_chunking_package_root() -> Path:
    """``phases/phase-3-chunking`` (contains ``phase_3_1/``, ``config/``, ``artifacts/``)."""
    return Path(__file__).resolve().parents[1]


@dataclass(frozen=True)
class Phase3ArtifactPaths:
    """Resolved paths under the Phase 3 chunking workspace."""

    root: Path
    chunks: Path
    chunks_validated: Path
    embeddings: Path
    indexes: Path
    logs: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any], phase3_root: Path | None = None) -> "Phase3ArtifactPaths":
        base = phase3_root or phase3_chunking_package_root()
        rel_root = Path(str(config.get("artifact_root", "artifacts")))
        root = rel_root if rel_root.is_absolute() else (base / rel_root).resolve()
        dirs = config.get("directories") or {}
        return cls(
            root=root,
            chunks=(root / str(dirs.get("chunks", "chunks"))).resolve(),
            chunks_validated=(root / str(dirs.get("chunks_validated", "chunks_validated"))).resolve(),
            embeddings=(root / str(dirs.get("embeddings", "embeddings"))).resolve(),
            indexes=(root / str(dirs.get("indexes", "indexes"))).resolve(),
            logs=(root / str(dirs.get("logs", "logs"))).resolve(),
        )

    def ensure_dirs(self) -> None:
        self.chunks.mkdir(parents=True, exist_ok=True)
        self.chunks_validated.mkdir(parents=True, exist_ok=True)
        self.embeddings.mkdir(parents=True, exist_ok=True)
        self.indexes.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    def handoff_report_path(self) -> Path:
        return self.root / "phase3_handoff_report.json"

    def dry_manifest_path(self) -> Path:
        return self.root / "phase3_1_dry_manifest.json"


@dataclass(frozen=True)
class Phase2ArtifactPaths:
    """Read-only view of Phase 2 ``artifacts/`` layout (clean + metadata)."""

    root: Path
    clean: Path
    metadata: Path
    quarantine: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "Phase2ArtifactPaths":
        root = resolve_phase2_artifact_root(config)
        return cls(
            root=root,
            clean=(root / "clean").resolve(),
            metadata=(root / "metadata").resolve(),
            quarantine=(root / "quarantine").resolve(),
        )

    def _slug_fs(self, scheme_slug: str) -> str:
        return scheme_slug.replace("/", "_")

    def clean_markdown_path(self, scheme_slug: str) -> Path:
        return self.clean / f"{self._slug_fs(scheme_slug)}.md"

    def clean_document_path(self, scheme_slug: str) -> Path:
        return self.clean / f"{self._slug_fs(scheme_slug)}.clean.json"

    def doc_metadata_path(self, scheme_slug: str) -> Path:
        return self.metadata / f"{self._slug_fs(scheme_slug)}.json"

    def quarantine_review_path(self, scheme_slug: str) -> Path:
        return self.quarantine / f"{self._slug_fs(scheme_slug)}.review.json"

    def phase2_corpus_manifest_path(self) -> Path:
        return self.root / "phase2_corpus_manifest.json"


def apply_config_env_overrides(config: dict[str, Any]) -> None:
    root = os.environ.get("PHASE3_ARTIFACT_ROOT", "").strip()
    if root:
        config["artifact_root"] = root
    p2 = os.environ.get("PHASE2_ARTIFACT_ROOT", "").strip()
    if p2:
        config["phase2_artifact_root"] = p2


def load_workspace_config(path: Path | None = None) -> dict[str, Any]:
    from chunking.config_load import load_chunking_config

    data = dict(load_chunking_config(path))
    apply_config_env_overrides(data)
    return data
