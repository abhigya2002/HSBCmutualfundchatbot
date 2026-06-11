"""Load Phase 4.4 hybrid retrieval configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from phase_4_1.config_load import load_config, phase4_retrieval_root


def default_hybrid_config_path() -> Path:
    env = os.environ.get("HYBRID_CONFIG_PATH", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return phase4_retrieval_root() / "config" / "hybrid.defaults.json"


def load_hybrid_config(path: Path | None = None) -> dict[str, Any]:
    p = path or default_hybrid_config_path()
    data = json.loads(p.read_text(encoding="utf-8"))
    cfg = load_config()
    merged = dict(cfg.get("hybrid") or {})
    merged.update(data)
    return merged
