"""Prohibited phrase checks with quoted-echo handling (P5-03, P5-13)."""

from __future__ import annotations

import re

from phase_5_1.handoff import ProhibitedPhrases


def strip_quoted_echo(text: str) -> str:
    """Remove quoted user-echo regions before advisory/comparison scans."""
    cleaned = re.sub(r'"[^"]*"', " ", text or "")
    cleaned = re.sub(r"'[^']*'", " ", cleaned)
    return re.sub(r"\s+", " ", cleaned).strip()


def _contains_pattern(text: str, pattern: str) -> bool:
    needle = pattern.strip().lower()
    if not needle:
        return False
    if " " in needle:
        return needle in text
    return re.search(rf"\b{re.escape(needle)}\b", text, re.IGNORECASE) is not None


def find_prohibited_phrases(text: str, prohibited: ProhibitedPhrases) -> list[str]:
    scan_text = strip_quoted_echo(text).lower()
    hits: list[str] = []

    for label, patterns in (
        ("advisory", prohibited.advisory_patterns),
        ("comparison", prohibited.comparison_patterns),
        ("projection", prohibited.projection_patterns),
    ):
        for pat in patterns:
            if _contains_pattern(scan_text, pat):
                hits.append(f"{label}:{pat.strip().lower()}")

    for raw in prohibited.regex_patterns:
        pat = raw.strip()
        if not pat:
            continue
        try:
            if re.search(pat, scan_text, re.IGNORECASE):
                hits.append(f"regex:{pat}")
        except re.error:
            continue
    return hits
