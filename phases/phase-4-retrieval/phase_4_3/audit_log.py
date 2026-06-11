"""Structured scheme resolution logging."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from phase_4_2.audit_log import redact_query
from phase_4_3.contracts import SchemeResolution

log = logging.getLogger("phase4_retrieval.scheme")


def log_scheme_resolution(
    result: SchemeResolution,
    *,
    query: str,
    extra: Mapping[str, Any] | None = None,
) -> None:
    payload: dict[str, Any] = {
        "event": "scheme_resolved",
        "ts_utc": datetime.now(timezone.utc).isoformat(),
        "status": result.status,
        "scheme": result.scheme,
        "confidence": result.confidence,
        "source_url": result.source_url,
        "citation_url_candidate": result.citation_url_candidate,
        "matched_schemes": result.matched_schemes,
        "reasons": result.reasons,
        "query_len": len(query),
        "query_redacted": redact_query(query)[:500],
    }
    if extra:
        payload.update(dict(extra))
    log.info("%s", json.dumps(payload, ensure_ascii=False))


def append_scheme_log_line(path: Path, result: SchemeResolution, *, query: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    row = result.to_dict()
    row["query_redacted"] = redact_query(query)
    row["logged_at_utc"] = datetime.now(timezone.utc).isoformat()
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(row, ensure_ascii=False) + "\n")
