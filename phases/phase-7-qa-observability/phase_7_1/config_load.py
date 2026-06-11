"""Load Phase 7.1 metrics configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any


def phase7_root() -> Path:
    return Path(__file__).resolve().parents[1]


def default_config_path() -> Path:
    env = os.environ.get("PHASE7_METRICS_CONFIG", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return phase7_root() / "config" / "metrics.defaults.json"


def load_config(path: Path | None = None) -> dict[str, Any]:
    p = path or default_config_path()
    cfg: dict[str, Any] = json.loads(p.read_text(encoding="utf-8"))
    if os.environ.get("PHASE7_API_BASE_URL", "").strip():
        cfg["api_base_url"] = os.environ["PHASE7_API_BASE_URL"].strip()
    return cfg


def resolve_path(cfg: dict[str, Any], key: str) -> Path:
    rel = str((cfg.get("paths") or {}).get(key) or "")
    p = Path(rel)
    if p.is_absolute():
        return p.resolve()
    return (phase7_root() / p).resolve()


def metrics_output_dir(cfg: dict[str, Any]) -> Path:
    rel = str((cfg.get("directories") or {}).get("metrics") or "artifacts/metrics")
    p = Path(rel)
    if p.is_absolute():
        out = p.resolve()
    else:
        out = (phase7_root() / p).resolve()
    out.mkdir(parents=True, exist_ok=True)
    return out
