"""Query helpers for keyword channel (P3-12 stopword detection)."""

from __future__ import annotations

from phase_3_5.normalize import tokenize

_STOPWORDS = frozenset(
    {
        "a",
        "an",
        "the",
        "is",
        "are",
        "was",
        "were",
        "what",
        "which",
        "who",
        "how",
        "of",
        "for",
        "to",
        "in",
        "on",
        "at",
        "and",
        "or",
        "me",
        "my",
        "this",
        "that",
        "it",
    },
)


def is_stopword_only_query(query: str) -> bool:
    """True when tokenized query has no terms outside stopwords (P3-12)."""
    terms = tokenize(query)
    if not terms:
        return True
    return all(t in _STOPWORDS for t in terms)
