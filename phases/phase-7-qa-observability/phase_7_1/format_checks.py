"""Format compliance helpers for Phase 7.1 metrics."""

from __future__ import annotations

import re
from typing import Any

from phase_7_1.allowlist import count_allowlist_violations, is_allowlisted

_FOOTER_PREFIX = "Last updated from sources:"


def sentence_count(text: str) -> int:
    cleaned = (text or "").strip()
    if not cleaned:
        return 0
    parts = re.split(r"[.!?]+", cleaned)
    return len([p for p in parts if p.strip()])


def assess_format_compliance(envelope: dict[str, Any]) -> dict[str, Any]:
    """Return per-response format compliance breakdown."""
    assistant = envelope.get("assistant") or {}
    body_text = str(assistant.get("body_text") or "").strip()
    citation_url = str(assistant.get("citation_url") or "").strip()
    footer_line = str(assistant.get("footer_line") or "")
    footer_date = str(assistant.get("footer_date") or "").strip()
    outcome_type = str(envelope.get("outcome_type") or "")

    sentences = sentence_count(body_text)
    has_body = bool(body_text)
    sentences_ok = sentences <= 3 if has_body else False
    citation_present = bool(citation_url)
    citation_allowlisted = is_allowlisted(citation_url) if citation_present else False
    footer_ok = _FOOTER_PREFIX in footer_line or bool(footer_date)
    validation_passed = bool(envelope.get("validation_passed"))
    assistant_validation = bool(assistant.get("validation_passed", validation_passed))
    allowlist_violations = count_allowlist_violations(citation_url)

    compliant = (
        outcome_type == "factual"
        and has_body
        and sentences_ok
        and citation_present
        and citation_allowlisted
        and footer_ok
        and validation_passed
        and allowlist_violations == 0
    )

    return {
        "outcome_type": outcome_type,
        "compliant": compliant,
        "sentence_count": sentences,
        "sentences_ok": sentences_ok,
        "citation_present": citation_present,
        "citation_allowlisted": citation_allowlisted,
        "footer_ok": footer_ok,
        "validation_passed": validation_passed,
        "assistant_validation_passed": assistant_validation,
        "allowlist_violations": allowlist_violations,
    }
