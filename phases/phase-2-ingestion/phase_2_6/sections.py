"""Derive chunk-boundary section offsets from normalized Markdown (Phase 2.6)."""

from __future__ import annotations

import re
from typing import Any

_HEADING = re.compile(r"^(#{1,6})\s+(.+)$", re.MULTILINE)


def markdown_heading_sections(text: str) -> list[dict[str, Any]]:
    """
    Split ``text`` into sections anchored at Markdown ATX headings.

    Returns a list of dicts with ``level``, ``title``, ``start_char``, ``end_char``
    where ``end_char`` is **exclusive** (Python slice ``text[start:end]``).
    """
    if not text:
        return [
            {
                "level": 0,
                "title": "(empty)",
                "start_char": 0,
                "end_char": 0,
            }
        ]

    matches = list(_HEADING.finditer(text))
    if not matches:
        return [
            {
                "level": 0,
                "title": "(document)",
                "start_char": 0,
                "end_char": len(text),
            }
        ]

    out: list[dict[str, Any]] = []
    if matches[0].start() > 0:
        out.append(
            {
                "level": 0,
                "title": "(preamble)",
                "start_char": 0,
                "end_char": matches[0].start(),
            }
        )

    for i, m in enumerate(matches):
        level = len(m.group(1))
        title = m.group(2).strip()
        start = m.start()
        if i + 1 < len(matches):
            end = matches[i + 1].start()
        else:
            end = len(text)
        out.append({"level": level, "title": title, "start_char": start, "end_char": end})

    return out
