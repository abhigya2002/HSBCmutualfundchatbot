"""Dedupe identical (and optional near-duplicate) chunk text per source URL (P3-11)."""

from __future__ import annotations

import hashlib
import re
from typing import Any, Mapping


def _normalize_for_dedupe(text: str) -> str:
    collapsed = re.sub(r"\s+", " ", text.strip())
    return collapsed.lower()


def _text_hash(text: str) -> str:
    return hashlib.sha256(_normalize_for_dedupe(text).encode("utf-8")).hexdigest()


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    if not a or not b:
        return 0.0
    return len(a & b) / len(a | b)


def _token_set(text: str) -> set[str]:
    return set(_normalize_for_dedupe(text).split())


def dedupe_chunks(
    chunks: list[dict[str, Any]],
    *,
    source_url: str,
    dedupe_identical: bool = True,
    near_dup_enabled: bool = False,
    near_dup_min_jaccard: float = 0.92,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Return deduplicated chunks and stats.

    Identical text (normalized) within the same ``source_url`` keeps the first chunk.
    """
    stats = {
        "input_count": len(chunks),
        "exact_duplicates_removed": 0,
        "near_duplicates_removed": 0,
        "output_count": 0,
    }
    if not dedupe_identical and not near_dup_enabled:
        stats["output_count"] = len(chunks)
        return chunks, stats

    seen_exact: set[str] = set()
    kept: list[dict[str, Any]] = []
    kept_token_sets: list[set[str]] = []

    for ch in chunks:
        text = str(ch.get("text") or "")
        if dedupe_identical:
            h = _text_hash(text)
            if h in seen_exact:
                stats["exact_duplicates_removed"] += 1
                continue
            seen_exact.add(h)

        if near_dup_enabled and kept:
            tokens = _token_set(text)
            is_near = False
            for prior_tokens in kept_token_sets:
                if _jaccard(tokens, prior_tokens) >= near_dup_min_jaccard:
                    is_near = True
                    break
            if is_near:
                stats["near_duplicates_removed"] += 1
                continue
            kept_token_sets.append(tokens)

        kept.append(ch)

    stats["output_count"] = len(kept)
    return kept, stats
