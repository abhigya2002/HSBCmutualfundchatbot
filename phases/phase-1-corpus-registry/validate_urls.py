#!/usr/bin/env python3
"""
Fetch each allowlisted URL (HEAD then GET fallback), record status and redirects.

Writes:
  - url-validation-report.json
  - url-validation-report.md

Respects robots.txt policy at architecture level; this script only checks reachability.
"""

from __future__ import annotations

import argparse
import json
import ssl
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from allowlist import canonicalize_url, get_canonical_urls, load_registry

USER_AGENT = "RAG-Corpus-Validator/1.0 (+phase-1-registry)"


@dataclass
class UrlCheckResult:
    id: int
    scheme: str
    url: str
    method_used: str
    http_status: int | None
    final_url: str | None
    redirect_off_allowlist: bool
    error: str | None
    content_type: str | None


def _try_request(url: str, method: str, timeout: float, ctx: ssl.SSLContext) -> tuple[int, str, str | None]:
    req = Request(url, method=method, headers={"User-Agent": USER_AGENT})
    with urlopen(req, timeout=timeout, context=ctx) as resp:
        status = getattr(resp, "status", 200)
        final = resp.geturl()
        ct = resp.headers.get_content_type() if resp.headers else None
        return int(status), final, ct


def check_one(entry: dict[str, object], timeout: float, ctx: ssl.SSLContext) -> UrlCheckResult:
    url = str(entry["url"])
    eid = int(entry["id"])
    slug = str(entry["scheme"])
    allow = set(get_canonical_urls())

    for method in ("HEAD", "GET"):
        try:
            status, final, ct = _try_request(url, method, timeout, ctx)
            try:
                cfinal = canonicalize_url(final)
                off = cfinal not in allow
            except Exception:
                off = True
            return UrlCheckResult(
                id=eid,
                scheme=slug,
                url=url,
                method_used=method,
                http_status=status,
                final_url=final,
                redirect_off_allowlist=off,
                error=None,
                content_type=ct,
            )
        except HTTPError as e:
            if e.code == 405 and method == "HEAD":
                continue
            return UrlCheckResult(
                id=eid,
                scheme=slug,
                url=url,
                method_used=method,
                http_status=e.code,
                final_url=getattr(e, "url", None),
                redirect_off_allowlist=False,
                error=str(e),
                content_type=None,
            )
        except URLError as e:
            if method == "HEAD":
                continue
            reason = e.reason if hasattr(e, "reason") else e
            return UrlCheckResult(
                id=eid,
                scheme=slug,
                url=url,
                method_used=method,
                http_status=None,
                final_url=None,
                redirect_off_allowlist=False,
                error=str(reason),
                content_type=None,
            )
        except OSError as e:
            if method == "HEAD":
                continue
            return UrlCheckResult(
                id=eid,
                scheme=slug,
                url=url,
                method_used=method,
                http_status=None,
                final_url=None,
                redirect_off_allowlist=False,
                error=str(e),
                content_type=None,
            )

    return UrlCheckResult(
        id=eid,
        scheme=slug,
        url=url,
        method_used="NONE",
        http_status=None,
        final_url=None,
        redirect_off_allowlist=False,
        error="HEAD and GET both failed",
        content_type=None,
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate allowlisted Groww URLs.")
    parser.add_argument("--timeout", type=float, default=20.0, help="Per-request timeout seconds")
    parser.add_argument(
        "--insecure",
        action="store_true",
        help="Disable TLS verification (dev only)",
    )
    args = parser.parse_args()
    base = Path(__file__).resolve().parent
    ctx = ssl.create_default_context()
    if args.insecure:
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE

    data = load_registry(base / "source_registry.json")
    results: list[UrlCheckResult] = []
    for entry in data["entries"]:
        results.append(check_one(entry, args.timeout, ctx))

    summary = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "total": len(results),
        "ok_2xx": sum(1 for r in results if r.http_status is not None and 200 <= r.http_status < 300),
        "redirect_off_allowlist": sum(1 for r in results if r.redirect_off_allowlist),
        "errors": sum(1 for r in results if r.error),
    }

    out_json = {"summary": summary, "results": [asdict(r) for r in results]}
    (base / "url-validation-report.json").write_text(
        json.dumps(out_json, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# URL validation report",
        "",
        f"Generated (UTC): `{summary['generated_at_utc']}`",
        "",
        "## Summary",
        "",
        "| Metric | Value |",
        "|--------|-------|",
        f"| Total URLs | {summary['total']} |",
        f"| HTTP 2xx | {summary['ok_2xx']} |",
        f"| Redirect final URL off allowlist | {summary['redirect_off_allowlist']} |",
        f"| Transport / other errors | {summary['errors']} |",
        "",
        "## Per URL",
        "",
        "| id | scheme | status | method | final_url | off-allowlist redirect | error |",
        "|----|--------|--------|--------|-----------|-------------------------|-------|",
    ]
    for r in results:
        fu = (r.final_url or "")[:100]
        lines.append(
            f"| {r.id} | `{r.scheme}` | {r.http_status} | {r.method_used} | {fu} | "
            f"{r.redirect_off_allowlist} | {r.error or ''} |"
        )
    (base / "url-validation-report.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    bad_redirect = summary["redirect_off_allowlist"] > 0
    bad_error = summary["errors"] > 0
    return 1 if (bad_redirect or bad_error) else 0


if __name__ == "__main__":
    raise SystemExit(main())
