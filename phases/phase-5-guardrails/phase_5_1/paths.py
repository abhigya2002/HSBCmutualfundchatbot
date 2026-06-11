"""Phase 5 artifact layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from phase_5_1.config_load import phase5_guardrails_root, resolve_config_relative, resolve_phase4_retrieval_root


@dataclass(frozen=True)
class GuardrailsArtifactPaths:
    root: Path
    eval: Path
    service: Path
    logs: Path
    templates: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any], guardrails_root: Path | None = None) -> "GuardrailsArtifactPaths":
        base = guardrails_root or phase5_guardrails_root()
        rel = Path(str(config.get("artifact_root", "artifacts")))
        root = rel if rel.is_absolute() else (base / rel).resolve()
        dirs = config.get("directories") or {}
        return cls(
            root=root,
            eval=(root / str(dirs.get("eval", "eval"))).resolve(),
            service=(root / str(dirs.get("service", "service"))).resolve(),
            logs=(root / str(dirs.get("logs", "logs"))).resolve(),
            templates=(root / str(dirs.get("templates", "templates"))).resolve(),
        )

    def ensure_dirs(self) -> None:
        self.eval.mkdir(parents=True, exist_ok=True)
        self.service.mkdir(parents=True, exist_ok=True)
        self.logs.mkdir(parents=True, exist_ok=True)
        self.templates.mkdir(parents=True, exist_ok=True)

    def dry_manifest_path(self) -> Path:
        return self.root / "phase5_1_dry_manifest.json"

    def handoff_validation_path(self) -> Path:
        return self.root / "phase5_1_handoff_validation.json"


@dataclass(frozen=True)
class Phase4HandoffPaths:
    retrieval_root: Path
    retrieval_artifacts: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "Phase4HandoffPaths":
        retrieval = resolve_phase4_retrieval_root(dict(config))
        return cls(
            retrieval_root=retrieval,
            retrieval_artifacts=(retrieval / "artifacts").resolve(),
        )

    def phase5_handoff_path(self, config: Mapping[str, Any]) -> Path:
        handoff = config.get("handoff_files") or {}
        rel = Path(str(handoff.get("phase5_retrieval_handoff") or ""))
        if rel.is_absolute():
            return rel.resolve()
        if str(rel).startswith(".."):
            return (phase5_guardrails_root() / rel).resolve()
        return (self.retrieval_artifacts / "service" / "phase5_retrieval_handoff.json").resolve()

    def default_handoff_path(self, config: Mapping[str, Any]) -> Path:
        configured = (config.get("handoff_files") or {}).get("phase5_retrieval_handoff")
        if configured:
            return self.phase5_handoff_path(config)
        return self.retrieval_artifacts / "service" / "phase5_retrieval_handoff.json"
