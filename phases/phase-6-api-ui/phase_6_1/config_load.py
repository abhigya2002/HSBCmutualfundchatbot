"""Load Phase 6 API/UI configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def phase6_api_ui_root() -> Path:
    return Path(__file__).resolve().parents[1]


def project_root() -> Path:
    return phase6_api_ui_root().parents[1]


def default_config_path() -> Path:
    env = os.environ.get("API_UI_CONFIG_PATH", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return phase6_api_ui_root() / "config" / "api.defaults.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or default_config_path()
    data: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    if os.environ.get("PHASE6_ARTIFACT_ROOT", "").strip():
        data["artifact_root"] = os.environ["PHASE6_ARTIFACT_ROOT"].strip()
    if os.environ.get("PHASE5_GUARDRAILS_ROOT", "").strip():
        data["phase5_guardrails_root"] = os.environ["PHASE5_GUARDRAILS_ROOT"].strip()
    return data


def resolve_phase5_guardrails_root(config: dict[str, Any]) -> Path:
    rel = Path(str(config.get("phase5_guardrails_root", "../phase-5-guardrails")))
    return rel if rel.is_absolute() else (phase6_api_ui_root() / rel).resolve()


def resolve_config_relative(path_str: str) -> Path:
    if not path_str:
        return phase6_api_ui_root()
    p = Path(path_str)
    if p.is_absolute():
        return p.resolve()
    return (phase6_api_ui_root() / p).resolve()
