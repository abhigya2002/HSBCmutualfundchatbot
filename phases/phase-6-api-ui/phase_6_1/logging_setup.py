"""Logging for Phase 6 API/UI."""

from __future__ import annotations

import logging
import sys
from typing import Any, Mapping


def setup_logging(config: Mapping[str, Any] | None = None) -> None:
    cfg = config or {}
    level = getattr(logging, str((cfg.get("logging") or {}).get("level", "INFO")).upper(), logging.INFO)
    log = logging.getLogger("phase6_api_ui")
    log.setLevel(level)
    if log.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    log.addHandler(handler)
    log.propagate = False
