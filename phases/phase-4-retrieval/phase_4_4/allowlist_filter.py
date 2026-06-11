"""Allowlist filtering for retrieval hits (P3-04)."""

from __future__ import annotations

from phase_4_1.registry_bridge import canonicalize_url, is_allowlisted_url


def canonicalize_source_url(url: str) -> str:
    try:
        return canonicalize_url(url)
    except Exception:
        return url.strip().rstrip("/").lower()


def is_allowlisted_source(url: str) -> bool:
    try:
        return is_allowlisted_url(url)
    except Exception:
        return False
