"""Load Phase 5 guardrails configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def phase5_guardrails_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_config_path() -> Path:
    env = os.environ.get("GUARDRAILS_CONFIG_PATH", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return phase5_guardrails_root() / "config" / "guardrails.defaults.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or default_config_path()
    data = json.loads(p.read_text(encoding="utf-8"))
    root = phase5_guardrails_root()
    if os.environ.get("PHASE5_ARTIFACT_ROOT", "").strip():
        data["artifact_root"] = os.environ["PHASE5_ARTIFACT_ROOT"].strip()
    if os.environ.get("PHASE4_RETRIEVAL_ROOT", "").strip():
        data["phase4_retrieval_root"] = os.environ["PHASE4_RETRIEVAL_ROOT"].strip()
    return data


def resolve_phase4_retrieval_root(config: dict[str, Any]) -> Path:
    rel = Path(str(config.get("phase4_retrieval_root", "../phase-4-retrieval")))
    return rel if rel.is_absolute() else (phase5_guardrails_root() / rel).resolve()


def resolve_config_relative(path_str: str, config_path: Path | None = None) -> Path:
    base = (config_path or default_config_path()).parent
    if not path_str:
        return base
    p = Path(path_str)
    if p.is_absolute():
        return p.resolve()
    return (phase5_guardrails_root() / p).resolve()
