"""Keyword-channel text normalization (P3-06). Does not modify generation text."""

from __future__ import annotations

import re
import unicodedata

_RUPEE_RE = re.compile(r"₹|\brupees?\b", re.I)
_PERCENT_RE = re.compile(r"(\d+(?:\.\d+)?)\s*%")
_MULTI_SPACE = re.compile(r"\s+")


def normalize_for_keyword_index(text: str) -> str:
    """
    Normalize currency and percent for BM25 tokenization only.

    - ``₹1,000`` → ``INR 1000``
    - ``0.48%`` → ``0.48 percent``
    """
    t = unicodedata.normalize("NFKC", text)
    t = _RUPEE_RE.sub(" INR ", t)
    t = re.sub(r"INR\s*([\d,]+(?:\.\d+)?)", r"INR \1", t)
    t = t.replace(",", "")
    t = _PERCENT_RE.sub(r"\1 percent", t)
    t = _MULTI_SPACE.sub(" ", t)
    return t.strip().lower()


def tokenize(text: str) -> list[str]:
    """Simple alphanumeric tokens for BM25."""
    normalized = normalize_for_keyword_index(text)
    return re.findall(r"[a-z0-9]+", normalized)


def expand_facet_phrases(text: str, facet_phrases: list[str]) -> str:
    """
    Append underscore variants of facet phrases present in text to boost retrieval.

    Example: if text contains ``exit load``, also index ``exit_load``.
    """
    lower = text.lower()
    extras: list[str] = []
    for phrase in facet_phrases:
        p = phrase.lower().strip()
        if not p:
            continue
        if p in lower:
            extras.append(p.replace(" ", "_").replace("-", "_"))
    if extras:
        return text + " " + " ".join(extras)
    return text
