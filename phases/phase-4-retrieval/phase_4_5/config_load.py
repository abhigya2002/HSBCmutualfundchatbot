"""Load Phase 4.5 re-rank configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from phase_4_1.config_load import load_config, phase4_retrieval_root


def default_rerank_config_path() -> Path:
    env = os.environ.get("RERANK_CONFIG_PATH", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return phase4_retrieval_root() / "config" / "rerank.defaults.json"


def load_rerank_config(path: Path | None = None) -> dict[str, Any]:
    p = path or default_rerank_config_path()
    data = json.loads(p.read_text(encoding="utf-8"))
    cfg = load_config()
    merged = dict(cfg.get("rerank") or {})
    merged.update(data)
    return merged
