"""Stable content hashing — strip volatile NAV/AUM/date lines before hash (Phase 1.3)."""

from __future__ import annotations

import hashlib
import re

from bs4 import BeautifulSoup

# Lines containing these patterns are excluded before hashing.
_VOLATILE_LINE_PATTERNS: tuple[re.Pattern[str], ...] = (
    re.compile(r"\bNAV\b", re.IGNORECASE),
    re.compile(r"\bAUM\b", re.IGNORECASE),
    re.compile(r"\bas\s+on\b", re.IGNORECASE),
    re.compile(r"\bas\s+at\b", re.IGNORECASE),
    re.compile(
        r"\b\d{1,2}\s+(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|jun(?:e)?|"
        r"jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|nov(?:ember)?|dec(?:ember)?)\s+\d{4}\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)\s+\d{1,2},?\s+\d{4}\b", re.IGNORECASE),
)


def strip_volatile_lines(text: str) -> str:
    """Remove lines with NAV, AUM, or 'as on <date>' style volatility."""
    kept: list[str] = []
    for line in text.splitlines():
        if any(p.search(line) for p in _VOLATILE_LINE_PATTERNS):
            continue
        kept.append(line)
    return "\n".join(kept)


def html_to_stable_text(html: str) -> str:
    """Extract visible text from HTML, dropping script/style noise before hashing."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)


def stable_content_hash(text: str) -> str:
    """SHA-256 of normalized text after volatile-line stripping."""
    cleaned = strip_volatile_lines(text)
    normalized = re.sub(r"\s+", " ", cleaned.strip())
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()
