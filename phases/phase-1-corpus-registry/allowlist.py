"""
Strict corpus allowlist: exactly 16 Groww HSBC scheme URLs.

Use for fetch gates, citation validators, and registry integrity checks.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, FrozenSet
from urllib.parse import urlparse, urlunparse

_REGISTRY_FILENAME = "source_registry.json"


class AllowlistError(ValueError):
    """Raised when a URL is not in the canonical allowlist or registry is invalid."""


def _package_dir() -> Path:
    return Path(__file__).resolve().parent


def canonicalize_url(url: str) -> str:
    """
    Normalize user or model-provided URLs for comparison.

    Rules: strip outer whitespace; https; lowercase host; drop default :443;
    strip query and fragment; remove trailing slash on path (except root).
    """
    raw = (url or "").strip()
    if not raw:
        raise AllowlistError("Empty URL")

    parsed = urlparse(raw)
    if not parsed.scheme or not parsed.netloc:
        if not parsed.scheme and parsed.path.startswith("//"):
            raw = "https:" + raw
            parsed = urlparse(raw)
        else:
            raise AllowlistError(f"Not a valid absolute URL: {url!r}")

    scheme = "https"
    host = (parsed.hostname or "").lower()
    if host.startswith("www."):
        host = host[4:]
    if host != "groww.in":
        raise AllowlistError(f"Host not allowed: {host!r}")

    path = parsed.path or ""
    path = re.sub(r"/+", "/", path)
    if len(path) > 1 and path.endswith("/"):
        path = path[:-1]

    normalized = urlunparse((scheme, host, path, "", "", ""))
    return normalized


def load_registry(path: Path | None = None) -> dict[str, Any]:
    """Load source_registry.json from this directory."""
    p = path or (_package_dir() / _REGISTRY_FILENAME)
    with open(p, encoding="utf-8") as f:
        return json.load(f)


def get_canonical_urls() -> tuple[str, ...]:
    """Return the 16 canonical URLs in registry order (stable)."""
    data = load_registry()
    entries = data.get("entries")
    if not isinstance(entries, list):
        raise AllowlistError("Registry missing 'entries' list")
    urls = tuple(str(e["url"]) for e in entries)
    if len(urls) != 16:
        raise AllowlistError(f"Expected 16 registry entries, got {len(urls)}")
    return urls


def allowlisted_urls_set() -> FrozenSet[str]:
    return frozenset(get_canonical_urls())


def is_allowlisted(url: str) -> bool:
    try:
        c = canonicalize_url(url)
    except AllowlistError:
        return False
    return c in allowlisted_urls_set()


def require_allowlisted(url: str) -> str:
    """Return canonical URL if allowlisted; else raise AllowlistError."""
    c = canonicalize_url(url)
    if c not in allowlisted_urls_set():
        raise AllowlistError(f"URL not in corpus allowlist: {url!r} -> {c!r}")
    return c


def validate_registry_integrity(data: dict[str, Any] | None = None) -> None:
    """
    Assert registry shape: 16 entries, unique schemes and URLs,
    source_type groww_scheme_page, active true, URLs match canonicalize_url.
    """
    data = data if data is not None else load_registry()
    entries = data.get("entries")
    if not isinstance(entries, list) or len(entries) != 16:
        raise AllowlistError(f"entries must be a list of length 16, got {entries!r}")

    seen_urls: set[str] = set()
    seen_schemes: set[str] = set()

    for e in entries:
        url = str(e.get("url", ""))
        scheme = str(e.get("scheme", ""))
        c = canonicalize_url(url)
        if c != url:
            raise AllowlistError(f"Stored url must be canonical form: {url!r} != {c!r}")
        if c in seen_urls:
            raise AllowlistError(f"Duplicate url: {c}")
        seen_urls.add(c)

        if scheme in seen_schemes:
            raise AllowlistError(f"Duplicate scheme slug: {scheme}")
        seen_schemes.add(scheme)

        if e.get("source_type") != "groww_scheme_page":
            raise AllowlistError(f"Invalid source_type: {e.get('source_type')!r}")
        if e.get("active") is not True:
            raise AllowlistError(f"Entry id={e.get('id')} must have active=true for closed corpus")

        expected_prefix = f"/mutual-funds/{scheme}"
        if urlparse(c).path != expected_prefix:
            raise AllowlistError(f"path {urlparse(c).path!r} does not match scheme slug {scheme!r}")

    extra = seen_urls - allowlisted_urls_set()
    if extra:
        raise AllowlistError(f"Internal error: url set mismatch {extra}")


def entry_by_scheme_slug(slug: str) -> dict[str, Any] | None:
    """Return registry entry dict for slug, or None."""
    for e in load_registry()["entries"]:
        if e.get("scheme") == slug:
            return e
    return None
