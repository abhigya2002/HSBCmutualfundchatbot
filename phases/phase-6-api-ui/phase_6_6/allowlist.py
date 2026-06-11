"""16 allowlisted HSBC Groww citation URLs (Phase 6.6 validation)."""

from __future__ import annotations

ALLOWLISTED_CITATION_URLS: tuple[str, ...] = (
    "https://groww.in/mutual-funds/hsbc-india-opportunities-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-value-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-large-and-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-equity-savings-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-infrastructure-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-multi-asset-allocation-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-focused-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-gold-etf-fof-direct-growth",
    "https://groww.in/mutual-funds/hsbc-india-export-opportunities-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-consumption-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-medium-duration-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-dynamic-bond-fund-direct-growth",
    "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
)

_ALLOWLIST_SET = frozenset(u.rstrip("/") for u in ALLOWLISTED_CITATION_URLS)


def normalize_url(url: str) -> str:
    return url.strip().rstrip("/")


def is_allowlisted(url: str) -> bool:
    if not url.strip():
        return False
    return normalize_url(url) in _ALLOWLIST_SET
