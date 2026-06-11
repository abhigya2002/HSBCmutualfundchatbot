"""Phase 4 artifact layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from phase_4_1.config_load import phase4_retrieval_root, resolve_phase3_chunking_root, resolve_phase3_indexing_root


@dataclass(frozen=True)
class RetrievalArtifactPaths:
    root: Path
    eval: Path
    service: Path
    logs: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any], retrieval_root: Path | None = None) -> "RetrievalArtifactPaths":
        base = retrieval_root or phase4_retrieval_root()
        rel = Path(str(config.get("artifact_root", "artifacts")))
        root = rel if rel.is_absolute() else (base / rel).resolve()
        dirs = config.get("directories") or {}
        return cls(
            root=root,
            eval=(root / str(dirs.get("eval", "eval"))).resolve(),
            service=(root / str(dirs.get("service", "service"))).resolve(),
            logs=(root / str(dirs.get("logs", "logs"))).resolve(),
        )

    def ensure_dirs(self) -> None:
        self.eval.mkdir(parents=True, exist_ok=True)
        self.service.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)

    def dry_manifest_path(self) -> Path:
        return self.root / "phase4_1_dry_manifest.json"

    def handoff_validation_path(self) -> Path:
        return self.root / "phase4_1_handoff_validation.json"


@dataclass(frozen=True)
class Phase3Paths:
    chunking_root: Path
    indexing_root: Path
    chunking_artifacts: Path
    indexing_artifacts: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "Phase3Paths":
        chunking = resolve_phase3_chunking_root(dict(config))
        indexing = resolve_phase3_indexing_root(dict(config))
        return cls(
            chunking_root=chunking,
            indexing_root=indexing,
            chunking_artifacts=(chunking / "artifacts").resolve(),
            indexing_artifacts=(indexing / "artifacts").resolve(),
        )

    def vector_active_path(self) -> Path:
        return self.chunking_artifacts / "indexes" / "vector" / "active.json"

    def keyword_active_path(self) -> Path:
        return self.indexing_artifacts / "indexes" / "keyword" / "active.json"

    def phase4_handoff_path(self) -> Path:
        return self.indexing_artifacts / "phase4_retrieval_handoff.json"

    def hybrid_contract_path(self) -> Path:
        return self.indexing_artifacts / "hybrid_retrieval_contract.json"

    def phase3_index_manifest_path(self) -> Path:
        return self.indexing_artifacts / "phase3_index_manifest.json"
