"""Load Phase 4.2 intent rules configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from phase_4_1.config_load import phase4_retrieval_root


def default_rules_path() -> Path:
    env = os.environ.get("INTENT_RULES_PATH", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return phase4_retrieval_root() / "config" / "intent.rules.json"


def load_intent_rules(path: Path | None = None) -> dict[str, Any]:
    p = path or default_rules_path()
    return json.loads(p.read_text(encoding="utf-8"))
