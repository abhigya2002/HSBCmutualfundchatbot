"""
Phase 2.3 — Primary content extraction from raw Groww HTML (BeautifulSoup).

Version tag for downstream ``doc_metadata`` (Phase 2.5).
"""

from __future__ import annotations

from dataclasses import dataclass

from bs4 import BeautifulSoup

EXTRACT_VERSION = "2.3.0"


@dataclass
class ExtractOutput:
    extract_status: str
    main_html: str
    text_length: int
    selector_used: str | None
    error: str | None = None


def _visible_text_length(element) -> int:
    return len(element.get_text("\n", strip=True))


def _detect_challenge_text(text_lower: str) -> bool:
    return any(
        p in text_lower
        for p in (
            "captcha",
            "unusual traffic",
            "are you a robot",
            "access denied",
            "cf-browser-verification",
        )
    )


def extract_main_fragment(html_bytes: bytes, encoding_hint: str | None = None) -> ExtractOutput:
    """
    Parse HTML and isolate main fund content.

    Groww mutual-fund pages embed substantial SSR under ``#root``; Next.js shell
    lives under ``#__next`` with often minimal static text — prefer ``#root``.
    """
    try:
        soup = BeautifulSoup(html_bytes, "html.parser", from_encoding=encoding_hint)
    except Exception as e:
        return ExtractOutput("parse_error", "", 0, None, str(e))

    target = None
    selector = None

    root = soup.find(id="root")
    if root is not None and _visible_text_length(root) > 200:
        target, selector = root, "#root"
    if target is None:
        main = soup.find("main") or soup.find(attrs={"role": "main"}) or soup.find("article")
        if main is not None and _visible_text_length(main) > 100:
            target, selector = main, main.name
    if target is None:
        nxt = soup.find(id="__next")
        if nxt is not None:
            target, selector = nxt, "#__next"
    if target is None:
        target, selector = soup.body if soup.body is not None else soup, "document"

    for tag in target.find_all(["script", "style", "noscript"]):
        tag.decompose()

    main_html = str(target)
    text = target.get_text("\n", strip=True)
    text_lower = text.lower()
    tl = len(text)

    if _detect_challenge_text(text_lower) or _detect_challenge_text(
        html_bytes[:200_000].decode("utf-8", errors="ignore").lower()
    ):
        if tl >= 2500:
            status = "partial"
        elif tl >= 400:
            status = "partial"
        else:
            status = "empty_shell"
    elif tl >= 6000 and ("expense" in text_lower or "nav" in text_lower or "₹" in text):
        status = "ok"
    elif tl >= 2500:
        status = "partial"
    elif tl >= 500:
        status = "partial"
    else:
        status = "empty_shell"

    return ExtractOutput(
        extract_status=status,
        main_html=main_html,
        text_length=tl,
        selector_used=selector,
        error=None,
    )
