"""Strip prompt-injection patterns from user queries (P4-11, P5-10)."""

from __future__ import annotations

import re
from dataclasses import dataclass

from phase_5_1.handoff import ProhibitedPhrases


@dataclass(frozen=True)
class QuerySanitizeResult:
    sanitized_query: str
    stripped_patterns: list[str]
    injection_detected: bool


def _compile_patterns(prohibited: ProhibitedPhrases) -> list[tuple[str, re.Pattern[str] | None]]:
    compiled: list[tuple[str, re.Pattern[str] | None]] = []
    for raw in prohibited.injection_patterns:
        pat = raw.strip()
        if not pat:
            continue
        compiled.append((pat, None))
    for raw in prohibited.regex_patterns:
        pat = raw.strip()
        if not pat:
            continue
        try:
            compiled.append((pat, re.compile(pat, re.IGNORECASE)))
        except re.error:
            continue
    return compiled


def sanitize_query(query: str, prohibited: ProhibitedPhrases) -> QuerySanitizeResult:
    text = query.strip()
    lowered = text.lower()
    stripped: list[str] = []
    for label, pattern in _compile_patterns(prohibited):
        if pattern is None:
            needle = label.lower()
            if needle in lowered:
                stripped.append(label)
                text = re.sub(re.escape(label), " ", text, flags=re.IGNORECASE)
                lowered = text.lower()
            continue
        if pattern.search(text):
            stripped.append(label)
            text = pattern.sub(" ", text)
            lowered = text.lower()
    text = re.sub(r"\s+", " ", text).strip()
    return QuerySanitizeResult(
        sanitized_query=text,
        stripped_patterns=stripped,
        injection_detected=bool(stripped),
    )


def contains_projection_language(query: str, prohibited: ProhibitedPhrases) -> list[str]:
    lowered = query.lower()
    hits: list[str] = []
    for pat in prohibited.projection_patterns:
        p = pat.strip().lower()
        if p and p in lowered:
            hits.append(p)
    for raw in prohibited.regex_patterns:
        try:
            if re.search(raw, query, re.IGNORECASE) and any(
                token in raw.lower() for token in ("earn", "get", "make", "return")
            ):
                hits.append(raw)
        except re.error:
            continue
    return hits
