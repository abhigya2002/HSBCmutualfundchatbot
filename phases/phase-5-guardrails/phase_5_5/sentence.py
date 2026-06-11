"""Sentence budget tokenizer (P5-04 semicolon edge case)."""

from __future__ import annotations

import re

_PRIMARY_SPLIT = re.compile(r"(?<=[.!?])\s+")


def count_sentences(text: str, *, count_semicolon_clauses: bool = True) -> int:
    """
    Heuristic sentence count for guardrail enforcement.

    Primary split: ``. ! ?`` boundaries.
    Semicolon rule (P5-04): within a period-delimited segment, each ``;`` clause
    counts as an additional sentence when ``count_semicolon_clauses`` is enabled.
    """
    stripped = (text or "").strip()
    if not stripped:
        return 0

    segments = [part.strip() for part in _PRIMARY_SPLIT.split(stripped) if part.strip()]
    if not segments:
        return 1

    if not count_semicolon_clauses:
        return len(segments)

    total = 0
    for segment in segments:
        if ";" in segment:
            clauses = [clause.strip() for clause in segment.split(";") if clause.strip()]
            total += max(len(clauses), 1)
        else:
            total += 1
    return total


def truncate_to_sentence_budget(text: str, max_sentences: int, *, count_semicolon_clauses: bool = True) -> str:
    stripped = (text or "").strip()
    if not stripped or max_sentences <= 0:
        return ""

    if count_semicolon_clauses and ";" in stripped and not _PRIMARY_SPLIT.search(stripped):
        clauses = [c.strip() for c in stripped.split(";") if c.strip()]
        return "; ".join(clauses[:max_sentences])

    parts = [part.strip() for part in _PRIMARY_SPLIT.split(stripped) if part.strip()]
    kept = parts[:max_sentences]
    return " ".join(kept)
