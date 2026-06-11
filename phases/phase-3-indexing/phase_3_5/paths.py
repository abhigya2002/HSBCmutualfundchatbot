"""Phase 3.5 keyword index artifact paths."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class IndexingArtifactPaths:
    root: Path
    keyword_indexes: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any], indexing_root: Path | None = None) -> "IndexingArtifactPaths":
        base = indexing_root or Path(__file__).resolve().parents[1]
        rel = Path(str(config.get("artifact_root", "artifacts")))
        root = rel if rel.is_absolute() else (base / rel).resolve()
        dirs = config.get("directories") or {}
        kw = str(dirs.get("keyword_indexes", "indexes/keyword"))
        return cls(root=root, keyword_indexes=(root / kw).resolve())

    def ensure_dirs(self) -> None:
        self.keyword_indexes.mkdir(parents=True, exist_ok=True)

    def keyword_version_dir(self, index_version: str) -> Path:
        safe = index_version.replace("/", "_").replace("\\", "_")
        return self.keyword_indexes / safe

    def keyword_active_pointer(self) -> Path:
        return self.keyword_indexes / "active.json"

    def keyword_build_report(self) -> Path:
        return self.root / "phase3_keyword_build_report.json"

    def hybrid_contract_path(self) -> Path:
        return self.root / "hybrid_retrieval_contract.json"
