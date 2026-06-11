"""Hyperlink policy checks (P5-01, P5-02, P5-08, P5-11)."""

from __future__ import annotations

import re
import unicodedata
from urllib.parse import urlparse

from phase_5_1.registry_bridge import canonicalize_url, is_allowlisted_url

_MARKDOWN_LINK = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
_BARE_URL = re.compile(r"(?:https?://[^\s)\]]+|(?<![/@])groww\.in/[^\s)\]]+)", re.IGNORECASE)


def normalize_url_text(url: str) -> str:
    """Unicode-normalize URL text and coerce groww host/path to canonical HTTPS form."""
    raw = unicodedata.normalize("NFKC", (url or "").strip())
    raw = raw.replace("\uFF03", "#").replace("\uFF0F", "/")
    if raw.startswith("groww.in"):
        raw = f"https://{raw}"
    return raw


def extract_markdown_link_targets(text: str) -> list[str]:
    return [match.group(1).strip() for match in _MARKDOWN_LINK.finditer(text or "")]


def extract_bare_urls(text: str) -> list[str]:
    return [match.group(0).strip() for match in _BARE_URL.finditer(text or "")]


def count_hyperlinks(text: str) -> int:
    return len(extract_markdown_link_targets(text)) + len(extract_bare_urls(text))


def strip_hyperlinks_from_text(text: str) -> str:
    cleaned = _MARKDOWN_LINK.sub("", text or "")
    cleaned = _BARE_URL.sub("", cleaned)
    return re.sub(r"\s{2,}", " ", cleaned).strip()


def validate_citation_url(url: str) -> tuple[bool, str, str]:
    normalized = normalize_url_text(url)
    try:
        canon = canonicalize_url(normalized)
    except Exception:
        return False, normalized, "citation_not_allowlisted"
    if not is_allowlisted_url(canon):
        return False, normalized, "citation_not_allowlisted"
    parsed = urlparse(canon)
    if parsed.scheme != "https" or parsed.netloc != "groww.in":
        return False, canon, "citation_host_or_scheme"
    return True, canon, ""
