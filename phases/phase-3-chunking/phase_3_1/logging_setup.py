"""Logging setup for Phase 3 chunking/index workspace (optional PII redaction)."""

from __future__ import annotations

import logging
import re
import sys
from typing import Any, Mapping

_REDACT_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b"), "[REDACTED_PAN]"),
    (re.compile(r"\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b"), "[REDACTED_CARD]"),
    (re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b"), "[REDACTED_EMAIL]"),
    (re.compile(r"\b(?:\+91[\s-]?)?[6-9]\d{9}\b"), "[REDACTED_PHONE]"),
    (re.compile(r"\b\d{4}[\s-]?\d{4}[\s-]?\d{4}\b"), "[REDACTED_AADHAAR]"),
)


class PIIRedactingFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        line = super().format(record)
        if getattr(record, "skip_redaction", False):
            return line
        for pattern, repl in _REDACT_PATTERNS:
            line = pattern.sub(repl, line)
        return line


def setup_phase3_logging(config: Mapping[str, Any] | None = None) -> None:
    cfg = config or {}
    log_cfg = cfg.get("logging") or {}
    level_name = str(log_cfg.get("level", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)
    redact = bool(log_cfg.get("redact_pii", True))

    log = logging.getLogger("phase3_chunking")
    log.setLevel(level)
    if log.handlers:
        return

    handler = logging.StreamHandler(sys.stderr)
    if redact:
        fmt = PIIRedactingFormatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    else:
        fmt = logging.Formatter("%(asctime)s %(levelname)s [%(name)s] %(message)s")
    handler.setFormatter(fmt)
    log.addHandler(handler)
    log.propagate = False
