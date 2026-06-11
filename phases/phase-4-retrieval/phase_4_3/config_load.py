"""Load Phase 4.3 scheme alias configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from phase_4_1.config_load import phase4_retrieval_root


def default_aliases_path() -> Path:
    env = os.environ.get("SCHEME_ALIASES_PATH", "").strip()
    if env:
        return Path(env).expanduser().resolve()
    return phase4_retrieval_root() / "config" / "scheme.aliases.json"


def load_scheme_aliases(path: Path | None = None) -> dict[str, Any]:
    p = path or default_aliases_path()
    return json.loads(p.read_text(encoding="utf-8"))
