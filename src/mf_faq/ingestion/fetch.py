"""Allowlist-gated HTTP fetch for refresh monitoring (no redirect follow)."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import httpx

from mf_faq.ingestion.config import HTTP_HEADERS, HTTP_TIMEOUT, REDIRECT_STATUS_CODES
from mf_faq.ingestion.sources import load_sources

log = logging.getLogger(__name__)


@dataclass
class PageFetchResult:
    url: str
    ok: bool
    status_code: int
    text: str
    error: str = ""
    is_redirect: bool = False
    is_not_found: bool = False


def _url_in_registry(url: str) -> bool:
    normalized = url.strip().rstrip("/")
    return any(entry.url == normalized for entry in load_sources())


def fetch_page_for_hash(url: str) -> PageFetchResult:
    """GET allowlisted URL with follow_redirects=False for governance checks."""
    if not _url_in_registry(url):
        return PageFetchResult(
            url=url,
            ok=False,
            status_code=0,
            text="",
            error="URL not in config/sources.yaml",
        )

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=False, headers=HTTP_HEADERS) as client:
            resp = client.get(url)
    except httpx.HTTPError as exc:
        log.error("fetch_failed url=%s error_type=%s", url, type(exc).__name__)
        return PageFetchResult(url=url, ok=False, status_code=0, text="", error=type(exc).__name__)

    if resp.status_code in REDIRECT_STATUS_CODES:
        log.error("redirect_detected url=%s status=%s", url, resp.status_code)
        return PageFetchResult(
            url=url,
            ok=False,
            status_code=resp.status_code,
            text="",
            error="redirect_not_allowed",
            is_redirect=True,
        )

    if resp.status_code == 404:
        log.error("not_found url=%s status=404", url)
        return PageFetchResult(
            url=url,
            ok=False,
            status_code=404,
            text="",
            error="not_found",
            is_not_found=True,
        )

    if resp.status_code != 200:
        log.error("http_error url=%s status=%s", url, resp.status_code)
        return PageFetchResult(
            url=url,
            ok=False,
            status_code=resp.status_code,
            text="",
            error=f"http_{resp.status_code}",
        )

    return PageFetchResult(
        url=url,
        ok=True,
        status_code=200,
        text=resp.text,
    )
