"""Load indexing configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def phase3_indexing_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_config_path() -> Path:
    env = os.environ.get("INDEXING_CONFIG_PATH", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return phase3_indexing_root() / "config" / "indexing.defaults.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or default_config_path()
    data = json.loads(p.read_text(encoding="utf-8"))
    root = os.environ.get("PHASE3_INDEXING_ARTIFACT_ROOT", "").strip()
    if root:
        data["artifact_root"] = root
    chunk_root = os.environ.get("PHASE3_CHUNKING_ROOT", "").strip()
    if chunk_root:
        data["phase3_chunking_root"] = chunk_root
    return data


def resolve_chunking_artifact_root(config: dict[str, Any]) -> Path:
    rel = Path(str(config.get("phase3_chunking_root", "../phase-3-chunking")))
    base = rel if rel.is_absolute() else (phase3_indexing_root() / rel).resolve()
    return (base / "artifacts").resolve()
