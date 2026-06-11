"""Load chunking defaults from JSON (optional env override)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Mapping


def phase3_chunking_root() -> Path:
    """Directory containing ``config/`` and ``chunking/``."""
    return Path(__file__).resolve().parents[1]


def default_chunking_config_path() -> Path:
    return phase3_chunking_root() / "config" / "chunking.defaults.json"


def load_chunking_config(path: Path | None = None) -> dict[str, Any]:
    env = os.environ.get("CHUNKING_CONFIG_PATH", "").strip()
    p = path or (Path(env) if env else default_chunking_config_path())
    if not p.exists():
        p = default_chunking_config_path()
    return json.loads(p.read_text(encoding="utf-8"))


def resolve_phase2_artifact_root(cfg: Mapping[str, Any]) -> Path:
    rel = Path(str(cfg.get("phase2_artifact_root", "../phase-2-ingestion/artifacts")))
    if rel.is_absolute():
        return rel.resolve()
    return (phase3_chunking_root() / rel).resolve()
