"""
Phase 2.4 — Turn extracted main HTML into chunker-friendly Markdown.

Preserves headings, lists, and simple tables; strips common Groww chrome;
Unicode NFKC + whitespace cleanup; optional corpus-wide boilerplate line drop.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

from bs4 import BeautifulSoup, NavigableString, Tag

NORMALIZER_VERSION = "2.4.0"

INLINE_TAGS = frozenset(
    {"span", "strong", "em", "b", "i", "small", "a", "code", "sup", "sub", "label", "mark"}
)

# Substrings in CSS module class names for obvious chrome (Groww MF pages).
CHROME_CLASS_HINTS: tuple[str, ...] = (
    "header2025_",
    "loggedOut_nav",
    "loggedOut_leftContainer",
    "loggedOut_hoverDiv",
    "dropdownUI_dropdownContainer",
    "footerContainer",
    "Footer_",
    "cookie",
    "Cookie",
    "consentBanner",
    "AppDownload",
    "bottomNavigation",
    "stickyTab",
    "notificationBar",
    "TrustSafety",
)

# Exact short lines often repeated across scheme pages (supplement corpus dedupe).
STATIC_BOILERPLATE_LINES: frozenset[str] = frozenset(
    {
        "We are hiring!",
        "Help",
        "Search Groww",
        "Download App",
        "Open App",
    }
)

_MAX_SINGLE_BLOCK_CHARS = 200_000


def _chrome_class_match(tag: Tag) -> bool:
    classes = tag.get("class")
    if not classes:
        return False
    blob = " ".join(str(c) for c in classes)
    return any(h in blob for h in CHROME_CLASS_HINTS)


def strip_chrome(soup: BeautifulSoup) -> None:
    """Remove nav/header/footer and heuristic chrome containers (in-place)."""
    for t in list(soup.find_all(["script", "style", "noscript"])):
        t.decompose()

    for t in list(soup.find_all(["nav", "header", "footer"])):
        t.decompose()

    for t in list(soup.find_all(attrs={"role": re.compile(r"^(navigation|banner|contentinfo)$", re.I)})):
        t.decompose()

    chrome_blocks = [t for t in soup.find_all(["div", "section"]) if _chrome_class_match(t)]
    chrome_blocks.sort(key=lambda x: len(list(x.descendants)))
    for t in chrome_blocks:
        t.decompose()


def normalize_unicode(text: str) -> str:
    """NFKC for stable comparison; keeps ₹ and ASCII digits."""
    return unicodedata.normalize("NFKC", text)


def _collapse_blank_lines(text: str) -> str:
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip() + "\n" if text.strip() else ""


def _inline_text(node: Tag) -> str:
    return normalize_unicode(node.get_text(" ", strip=True))


def _direct_child_tags(node: Tag) -> list[Tag]:
    return [c for c in node.children if isinstance(c, Tag)]


def _emit_table(table: Tag) -> str:
    rows_out: list[str] = []
    for tr in table.find_all("tr"):
        if tr.find_parent("table") is not table:
            continue
        cells = tr.find_all(["th", "td"], recursive=False)
        if not cells:
            continue
        row = [re.sub(r"\s+", " ", _inline_text(td).strip()) for td in cells]
        if not any(row):
            continue
        rows_out.append("| " + " | ".join(row) + " |")
    if not rows_out:
        return ""
    width = rows_out[0].count("|") - 1
    sep = "| " + " | ".join(["---"] * max(width, 1)) + " |"
    if len(rows_out) == 1:
        return rows_out[0] + "\n" + sep + "\n\n"
    return rows_out[0] + "\n" + sep + "\n" + "\n".join(rows_out[1:]) + "\n\n"


def _emit_list(tag: Tag, ordered: bool) -> str:
    lines: list[str] = []
    for i, li in enumerate(_direct_child_tags(tag), start=1):
        if li.name != "li":
            continue
        inner = emit_markdown(li).strip()
        inner = re.sub(r"\n+", " ", inner)
        prefix = f"{i}. " if ordered else "- "
        if inner:
            lines.append(prefix + inner)
    return ("\n".join(lines) + "\n\n") if lines else ""


def emit_markdown(node: Tag | BeautifulSoup) -> str:
    """Emit lightweight Markdown from a subtree."""
    chunks: list[str] = []
    for child in node.children:
        chunks.append(_emit_node(child))
    return "".join(chunks)


def _emit_node(node: Tag | NavigableString | BeautifulSoup) -> str:
    if isinstance(node, NavigableString):
        t = str(node)
        if not t.strip():
            return ""
        return normalize_unicode(t)

    if not isinstance(node, Tag):
        return ""

    name = node.name
    if name in ("script", "style", "noscript"):
        return ""
    if name == "br":
        return "\n"
    if name in INLINE_TAGS:
        return emit_markdown(node)

    if name in ("h1", "h2", "h3", "h4", "h5", "h6"):
        lev = int(name[1])
        text = _inline_text(node).strip()
        if not text:
            return ""
        return ("#" * lev) + " " + text + "\n\n"

    if name in ("ul",):
        return _emit_list(node, ordered=False)
    if name in ("ol",):
        return _emit_list(node, ordered=True)

    if name == "table":
        return _emit_table(node)

    if name in ("p", "blockquote"):
        inner = emit_markdown(node).strip()
        if not inner:
            return ""
        return inner + "\n\n"

    if name in ("div", "section", "article", "main", "span"):
        inner = emit_markdown(node)
        return inner if inner else ""

    if name == "li":
        return emit_markdown(node)

    return emit_markdown(node)


def fragment_root(soup: BeautifulSoup) -> Tag:
    """Prefer ``body`` so we walk the full extracted fragment."""
    if soup.body is not None:
        return soup.body
    first = soup.find(True)
    if isinstance(first, Tag):
        return first
    return soup.new_tag("div")


@dataclass
class NormalizeOutput:
    markdown: str
    normalize_status: str
    char_count: int
    warnings: list[str] = field(default_factory=list)
    lines_removed_static: int = 0
    lines_removed_corpus: int = 0


def _filter_lines(md: str, blocklist: frozenset[str]) -> tuple[str, int]:
    removed = 0
    kept: list[str] = []
    for line in md.splitlines():
        st = line.strip()
        if st in blocklist:
            removed += 1
            continue
        kept.append(line)
    return _collapse_blank_lines("\n".join(kept)), removed


def normalize_extracted_html(
    html_bytes: bytes,
    *,
    encoding_hint: str | None = None,
    corpus_line_blocklist: frozenset[str] | None = None,
) -> NormalizeOutput:
    """
    Parse extracted main HTML, strip chrome, emit Markdown, normalize unicode/whitespace.
    """
    warnings: list[str] = []
    soup = BeautifulSoup(html_bytes, "html.parser", from_encoding=encoding_hint)
    strip_chrome(soup)
    root = fragment_root(soup)
    md = emit_markdown(root)
    md = _collapse_blank_lines(md)

    md, static_removed = _filter_lines(md, STATIC_BOILERPLATE_LINES)
    corpus_removed = 0
    if corpus_line_blocklist:
        md, corpus_removed = _filter_lines(md, corpus_line_blocklist)

    if len(md) > _MAX_SINGLE_BLOCK_CHARS:
        warnings.append(f"truncated_markdown>{_MAX_SINGLE_BLOCK_CHARS}")
        md = md[:_MAX_SINGLE_BLOCK_CHARS] + "\n\n<!-- truncated -->\n"

    char_count = len(md)
    if char_count == 0:
        return NormalizeOutput(
            "",
            "empty",
            0,
            warnings=["no_text_after_strip"],
            lines_removed_static=static_removed,
            lines_removed_corpus=corpus_removed,
        )

    status = "ok" if char_count >= 800 else "partial"
    return NormalizeOutput(
        md,
        status,
        char_count,
        warnings=warnings,
        lines_removed_static=static_removed,
        lines_removed_corpus=corpus_removed,
    )


def build_corpus_boilerplate_lines(markdowns: list[str], *, min_doc_coverage: int) -> frozenset[str]:
    """
    Lines that appear as a full stripped line in at least ``min_doc_coverage`` documents
    and look like menu/chrome (short, no % / ₹ / heavy digits).
    """
    if not markdowns or min_doc_coverage <= 0:
        return frozenset()

    def line_candidates(text: str) -> set[str]:
        out: set[str] = set()
        for line in text.splitlines():
            s = line.strip()
            if 3 <= len(s) <= 120 and s not in STATIC_BOILERPLATE_LINES:
                if "%" in s or "₹" in s or re.search(r"\d{3,}", s):
                    continue
                if re.search(r"\d\.\d", s):  # e.g. expense ratios like 0.5
                    continue
                out.add(s)
        return out

    per_doc_sets = [line_candidates(t) for t in markdowns]
    freq: dict[str, int] = {}
    for s in per_doc_sets:
        for line in s:
            freq[line] = freq.get(line, 0) + 1

    block = {ln for ln, c in freq.items() if c >= min_doc_coverage}
    return frozenset(block)
