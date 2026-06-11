"""Allowlist-gated HTTP fetch with redirect validation and retries."""

from __future__ import annotations

import logging
import random
import time
from dataclasses import dataclass, field
from typing import Any, Mapping
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from common.registry_bridge import canonicalize_url, is_allowlisted_url

log = logging.getLogger("phase2_ingestion.phase_2_2.fetch")


@dataclass
class FetchResult:
    request_url: str
    final_url: str | None = None
    http_status: int | None = None
    content_type: str | None = None
    body: bytes = b""
    error: str | None = None
    retries_used: int = 0
    captcha_suspect: bool = False
    login_shell_suspect: bool = False
    redirect_ok: bool = False
    notes: list[str] = field(default_factory=list)


def _http_settings(config: Mapping[str, Any]) -> dict[str, Any]:
    return dict(config.get("http") or {})


def _read_body_limited(resp: Any, max_bytes: int) -> bytes:
    buf = bytearray()
    while True:
        chunk = resp.read(65536)
        if not chunk:
            break
        buf.extend(chunk)
        if len(buf) > max_bytes:
            raise ValueError(f"Response body exceeds max_body_bytes ({max_bytes})")
    return bytes(buf)


def _detect_challenge(html_lower: str) -> tuple[bool, bool]:
    captcha = any(
        x in html_lower
        for x in (
            "captcha",
            "cf-browser-verification",
            "unusual traffic",
            "are you a robot",
            "enable javascript",
        )
    )
    login = "sign in to continue" in html_lower or "log in to continue" in html_lower
    return captcha, login


def fetch_allowlisted_url(url: str, config: Mapping[str, Any]) -> FetchResult:
    """
    GET ``url`` only if it is allowlisted; ensure final URL (after redirects) stays allowlisted.
    """
    if not is_allowlisted_url(url):
        return FetchResult(request_url=url, error="URL not in corpus allowlist (pre-flight)")

    http = _http_settings(config)
    timeout = float(http.get("timeout_seconds", 20.0))
    max_retries = int(http.get("max_retries", 3))
    backoff = float(http.get("backoff_base_seconds", 1.0))
    max_body = int(http.get("max_body_bytes", 16_777_216))
    ua = str(config.get("user_agent") or "RAG-Ingestion/1.0")

    expected = canonicalize_url(url)
    last_error: str | None = None

    for attempt in range(max_retries + 1):
        try:
            req = Request(url, method="GET", headers={"User-Agent": ua, "Accept": "text/html,*/*;q=0.8"})
            with urlopen(req, timeout=timeout) as resp:
                status = int(getattr(resp, "status", 200))
                final = resp.geturl()
                ctype = resp.headers.get_content_type() if resp.headers else None
                body = _read_body_limited(resp, max_body)

            try:
                final_c = canonicalize_url(final)
            except Exception as e:
                return FetchResult(
                    request_url=url,
                    final_url=final,
                    http_status=status,
                    content_type=ctype,
                    body=body,
                    error=f"Final URL failed canonicalization: {e}",
                    retries_used=attempt,
                )

            if final_c != expected:
                return FetchResult(
                    request_url=url,
                    final_url=final,
                    http_status=status,
                    content_type=ctype,
                    body=body,
                    error=f"Redirect left allowlisted path: {final_c!r} != {expected!r}",
                    retries_used=attempt,
                )

            if not is_allowlisted_url(final_c):
                return FetchResult(
                    request_url=url,
                    final_url=final,
                    http_status=status,
                    content_type=ctype,
                    body=body,
                    error="Final URL not in allowlist set",
                    retries_used=attempt,
                )

            html_lower = body[: min(500_000, len(body))].decode("utf-8", errors="ignore").lower()
            captcha, login = _detect_challenge(html_lower)

            return FetchResult(
                request_url=url,
                final_url=final_c,
                http_status=status,
                content_type=ctype,
                body=body,
                retries_used=attempt,
                captcha_suspect=captcha,
                login_shell_suspect=login,
                redirect_ok=True,
            )

        except HTTPError as e:
            last_error = f"HTTP {e.code}: {e.reason}"
            if e.code in (429, 500, 502, 503, 504) and attempt < max_retries:
                sleep_s = backoff * (2**attempt) + random.uniform(0, 0.5)
                log.warning("Retry %s after %s (sleep %.1fs)", url, last_error, sleep_s)
                time.sleep(sleep_s)
                continue
            return FetchResult(request_url=url, error=last_error, retries_used=attempt)

        except (URLError, OSError, TimeoutError, ValueError) as e:
            last_error = str(e)
            if attempt < max_retries:
                sleep_s = backoff * (2**attempt) + random.uniform(0, 0.5)
                log.warning("Retry %s after %s (sleep %.1fs)", url, last_error, sleep_s)
                time.sleep(sleep_s)
                continue
            return FetchResult(request_url=url, error=last_error, retries_used=attempt)

    return FetchResult(request_url=url, error=last_error or "unknown fetch failure", retries_used=max_retries)
