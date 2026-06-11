"""Logging for Phase 4 retrieval."""

from __future__ import annotations

import logging
import re
import sys
from typing import Any, Mapping

_REDACT = (
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"), "[REDACTED_PAN]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
)


def setup_logging(config: Mapping[str, Any] | None = None) -> None:
    cfg = config or {}
    level = getattr(logging, str((cfg.get("logging") or {}).get("level", "INFO")).upper(), logging.INFO)
    log = logging.getLogger("phase4_retrieval")
    log.setLevel(level)
    if log.handlers:
        return
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s"))
    log.addHandler(handler)
    log.propagate = False
