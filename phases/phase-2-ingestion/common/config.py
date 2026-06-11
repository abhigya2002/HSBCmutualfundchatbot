"""Load ingestion configuration from JSON with optional environment overrides."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping


def phase2_ingestion_root() -> Path:
    """``phases/phase-2-ingestion`` (contains ``common/``, ``config/``, ``phase_2_*``, ``artifacts/``)."""
    return Path(__file__).resolve().parents[1]


def default_config_path() -> Path:
    override = os.environ.get("INGESTION_CONFIG_PATH")
    if override:
        return Path(override).expanduser().resolve()
    return phase2_ingestion_root() / "config" / "ingestion.defaults.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or default_config_path()
    with open(p, encoding="utf-8") as f:
        data: dict[str, Any] = json.load(f)
    _apply_env_overrides(data)
    return data


def _apply_env_overrides(data: dict[str, Any]) -> None:
    root = os.environ.get("INGESTION_ARTIFACT_ROOT")
    if root:
        data["artifact_root"] = root
    ua = os.environ.get("INGESTION_USER_AGENT")
    if ua:
        data["user_agent"] = ua
    to = os.environ.get("INGESTION_TIMEOUT_SECONDS")
    if to:
        http = data.setdefault("http", {})
        http["timeout_seconds"] = float(to)


def get_http_settings(config: Mapping[str, Any]) -> dict[str, Any]:
    return dict(config.get("http") or {})
