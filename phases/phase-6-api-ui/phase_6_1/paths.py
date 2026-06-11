"""Phase 6 artifact and workspace layout."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from phase_6_1.config_load import phase6_api_ui_root, resolve_config_relative, resolve_phase5_guardrails_root


@dataclass(frozen=True)
class ApiUiArtifactPaths:
    root: Path
    eval: Path
    service: Path
    logs: Path
    api: Path
    ui: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any], api_ui_root: Path | None = None) -> "ApiUiArtifactPaths":
        base = api_ui_root or phase6_api_ui_root()
        rel = Path(str(config.get("artifact_root", "artifacts")))
        root = rel if rel.is_absolute() else (base / rel).resolve()
        dirs = config.get("directories") or {}
        return cls(
            root=root,
            eval=(root / str(dirs.get("eval", "eval"))).resolve(),
            service=(root / str(dirs.get("service", "service"))).resolve(),
            logs=(root / str(dirs.get("logs", "logs"))).resolve(),
            api=(root / str(dirs.get("api", "api"))).resolve(),
            ui=(root / str(dirs.get("ui", "ui"))).resolve(),
        )

    def ensure_dirs(self) -> None:
        for path in (self.eval, self.service, self.logs, self.api, self.ui):
            path.mkdir(parents=True, exist_ok=True)

    def dry_manifest_path(self) -> Path:
        return self.root / "phase6_1_dry_manifest.json"

    def handoff_validation_path(self) -> Path:
        return self.root / "phase6_1_handoff_validation.json"


@dataclass(frozen=True)
class Phase5HandoffPaths:
    guardrails_root: Path
    guardrails_artifacts: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any]) -> "Phase5HandoffPaths":
        guardrails = resolve_phase5_guardrails_root(dict(config))
        return cls(
            guardrails_root=guardrails,
            guardrails_artifacts=(guardrails / "artifacts").resolve(),
        )

    def phase6_generation_handoff_path(self, config: Mapping[str, Any]) -> Path:
        handoff = config.get("handoff_files") or {}
        rel = Path(str(handoff.get("phase6_generation_handoff") or ""))
        if rel.is_absolute():
            return rel.resolve()
        if str(rel).startswith(".."):
            return (phase6_api_ui_root() / rel).resolve()
        return (self.guardrails_artifacts / "service" / "phase6_generation_handoff.json").resolve()
