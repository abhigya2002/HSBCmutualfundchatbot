"""Load Phase 4 retrieval configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def phase4_retrieval_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_config_path() -> Path:
    env = os.environ.get("RETRIEVAL_CONFIG_PATH", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return phase4_retrieval_root() / "config" / "retrieval.defaults.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or default_config_path()
    data = json.loads(p.read_text(encoding="utf-8"))
    if os.environ.get("PHASE4_RETRIEVAL_ARTIFACT_ROOT", "").strip():
        data["artifact_root"] = os.environ["PHASE4_RETRIEVAL_ARTIFACT_ROOT"].strip()
    if os.environ.get("PHASE3_CHUNKING_ROOT", "").strip():
        data["phase3_chunking_root"] = os.environ["PHASE3_CHUNKING_ROOT"].strip()
    if os.environ.get("PHASE3_INDEXING_ROOT", "").strip():
        data["phase3_indexing_root"] = os.environ["PHASE3_INDEXING_ROOT"].strip()
    return data


def resolve_phase3_chunking_root(config: dict[str, Any]) -> Path:
    rel = Path(str(config.get("phase3_chunking_root", "../phase-3-chunking")))
    return rel if rel.is_absolute() else (phase4_retrieval_root() / rel).resolve()


def resolve_phase3_indexing_root(config: dict[str, Any]) -> Path:
    rel = Path(str(config.get("phase3_indexing_root", "../phase-3-indexing")))
    return rel if rel.is_absolute() else (phase4_retrieval_root() / rel).resolve()
