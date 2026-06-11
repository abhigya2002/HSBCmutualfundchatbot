"""
Detect Markdown table blocks so chunkers do not split mid-row.

A *table block* is a maximal run of consecutive non-empty lines that each contain ``|``.
"""

from __future__ import annotations

import re
from typing import Iterator


def _is_table_line(line: str) -> bool:
    s = line.strip()
    return bool(s) and "|" in s


def iter_table_spans_in_text(text: str) -> Iterator[tuple[int, int]]:
    """
    Yield ``(start, end_exclusive)`` spans covering each contiguous table block.
    """
    lines = text.splitlines(keepends=True)
    pos = 0
    i = 0
    while i < len(lines):
        if not _is_table_line(lines[i]):
            pos += len(lines[i])
            i += 1
            continue
        start = pos
        while i < len(lines) and _is_table_line(lines[i]):
            pos += len(lines[i])
            i += 1
        yield (start, pos)


def _gaps_between_tables(text: str, tables: list[tuple[int, int]]) -> Iterator[tuple[int, int]]:
    tables = sorted(tables)
    cur = 0
    for ts, te in tables:
        if cur < ts:
            yield (cur, ts)
        cur = max(cur, te)
    if cur < len(text):
        yield (cur, len(text))


def split_double_newline_spans(fragment: str, base: int) -> list[tuple[int, int]]:
    """Non-empty paragraph spans inside ``fragment`` mapped to absolute offsets ``+ base``."""
    out: list[tuple[int, int]] = []
    start = 0
    for m in re.finditer(r"\n\s*\n+", fragment):
        chunk = fragment[start : m.start()]
        if chunk.strip():
            out.append((base + start, base + m.start()))
        start = m.end()
    tail = fragment[start:]
    if tail.strip():
        out.append((base + start, base + len(fragment)))
    return out


def atomic_char_spans(text: str) -> list[tuple[int, int]]:
    """
    Partition ``text`` into atomic spans: whole table blocks, then paragraphs
    (split on blank lines) in non-table regions.
    """
    tables = list(iter_table_spans_in_text(text))
    units: list[tuple[int, int]] = list(tables)
    for gs, ge in _gaps_between_tables(text, tables):
        sub = text[gs:ge]
        if not sub.strip():
            continue
        units.extend(split_double_newline_spans(sub, gs))
    units.sort(key=lambda x: x[0])
    return units


def split_span_by_sentences(text: str, span: tuple[int, int], max_chars: int) -> list[tuple[int, int]]:
    """If ``span`` is longer than ``max_chars``, split on whitespace-friendly boundaries."""
    a, b = span
    frag = text[a:b]
    if len(frag) <= max_chars:
        return [span]
    out: list[tuple[int, int]] = []
    cur = 0
    n = len(frag)
    while cur < n:
        end = min(n, cur + max_chars)
        if end < n:
            cut = frag.rfind(" ", cur, end)
            if cut <= cur:
                cut = end
            end = cut
        out.append((a + cur, a + end))
        cur = end
        while cur < n and frag[cur].isspace():
            cur += 1
    return out or [span]
