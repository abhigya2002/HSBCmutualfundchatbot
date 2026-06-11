"""Logging for Phase 5 guardrails."""

from __future__ import annotations

import logging
import sys
from typing import Any, Mapping


def setup_logging(config: Mapping[str, Any] | None = None) -> None:
    cfg = config or {}
    level = getattr(logging, str((cfg.get("logging") or {}).get("level", "INFO")).upper(), logging.INFO)
    log = logging.getLogger("phase5_guardrails")
    log.setLevel(level)
    if log.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    log.addHandler(handler)
    log.propagate = False
