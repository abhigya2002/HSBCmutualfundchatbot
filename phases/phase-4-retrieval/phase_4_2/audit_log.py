"""Structured intent logging (no PII)."""

from __future__ import annotations

import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from phase_4_2.contracts import IntentResult

log = logging.getLogger("phase4_retrieval.intent")

_PAN = re.compile(r"\b[A-Z]{5}[0-9]{4}[A-Z]\b")
_EMAIL = re.compile(r"\b[\w.+-]+@[\w.-]+\.[A-Za-z]{2,}\b")


def redact_query(text: str) -> str:
    t = _PAN.sub("[REDACTED_PAN]", text)
    return _EMAIL.sub("[REDACTED_EMAIL]", t)


def log_intent_result(
    result: IntentResult,
    *,
    query: str,
    session_id: str | None = None,
    extra: Mapping[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "event": "intent_classified",
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "intent": result.intent,
        "action": result.action,
        "confidence": result.confidence,
        "policy_code": result.policy_code,
        "facet": result.facet,
        "reasons": result.reasons,
        "skip_retrieval": result.skip_retrieval,
        "query_len": len(query),
        "query_redacted": redact_query(query)[:500],
    }
    if session_id:
        payload["session_id"] = session_id
    if extra:
        payload.update(dict(extra))
    log.info("%s", json.dumps(payload, ensure_ascii=False))


def append_intent_log_line(path: Path, result: IntentResult, *, query: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = result.to_dict()
    row["query_redacted"] = redact_query(query)
    row["logged_at_utc"] = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
