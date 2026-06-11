"""Persist raw HTML bytes and crawl sidecar JSON."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from common.paths import ArtifactPaths

from phase_2_2.fetcher import FetchResult


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def persist_fetch(
    paths: ArtifactPaths,
    scheme_slug: str,
    source_url: str,
    result: FetchResult,
) -> dict[str, Any]:
    """
    Write ``{slug}.html`` when response is usable (2xx + html-ish body).
    Always write ``{slug}.crawl.json`` sidecar with audit fields.
    """
    paths.raw.mkdir(parents=True, exist_ok=True)
    crawl: dict[str, Any] = {
        "scheme": scheme_slug,
        "source_url": source_url,
        "fetched_at_utc": _utc_now_iso(),
        "http_status": result.http_status,
        "final_url": result.final_url,
        "content_type": result.content_type,
        "content_length": len(result.body),
        "sha256": hashlib.sha256(result.body).hexdigest() if result.body else None,
        "retries_used": result.retries_used,
        "error": result.error,
        "captcha_suspect": result.captcha_suspect,
        "login_shell_suspect": result.login_shell_suspect,
        "redirect_ok": result.redirect_ok,
    }

    html_path = paths.raw_html_path(scheme_slug)
    crawl_path = paths.crawl_meta_path(scheme_slug)

    ok_fetch = result.error is None and result.http_status is not None and 200 <= result.http_status < 300
    is_html = (result.content_type or "").lower().split(";")[0].strip() in ("text/html", "application/xhtml+xml")
    if ok_fetch and result.body and is_html:
        html_path.write_bytes(result.body)
        crawl["raw_html_path"] = str(html_path)
        crawl["fetch_status"] = (
            "challenge_suspect"
            if (result.captcha_suspect or result.login_shell_suspect)
            else "ok"
        )
    elif ok_fetch and result.body and not is_html:
        crawl["fetch_status"] = "non_html"
        crawl["note"] = "Body saved only in crawl record; unexpected content-type for HTML corpus."
    else:
        crawl["fetch_status"] = "failed"
        if html_path.exists():
            html_path.unlink()

    crawl_path.write_text(json.dumps(crawl, indent=2), encoding="utf-8")
    crawl["crawl_json_path"] = str(crawl_path)
    return crawl
