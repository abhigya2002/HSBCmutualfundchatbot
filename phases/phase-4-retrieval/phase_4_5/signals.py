"""Interpretable re-ranking signals (Phase 4.5)."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Mapping

from phase_4_2.contracts import IntentResult
from phase_4_2.config_load import load_intent_rules
from phase_4_3.contracts import SchemeResolution
from phase_4_4.contracts import RetrievalCandidate

_QUERY_STOP = frozenset(
    {
        "what",
        "is",
        "the",
        "of",
        "for",
        "a",
        "an",
        "in",
        "on",
        "and",
        "or",
        "hsbc",
        "fund",
        "direct",
        "growth",
        "mutual",
        "tell",
        "me",
        "about",
    },
)


def _tokenize(text: str) -> set[str]:
    t = text.lower()
    t = re.sub(r"[^\w\s%]", " ", t)
    toks = {w for w in t.split() if len(w) >= 2 and w not in _QUERY_STOP}
    return toks


def lexical_overlap(query: str, chunk_text: str) -> float:
    q = _tokenize(query)
    if not q:
        return 0.0
    c = _tokenize(chunk_text)
    if not c:
        return 0.0
    return len(q & c) / len(q)


def _facet_keywords(facet_code: str, rules: Mapping[str, Any]) -> list[str]:
    facets = rules.get("factual_facets") or {}
    facet = facets.get(facet_code) or {}
    return [str(k).lower() for k in (facet.get("keywords") or [])]


def facet_match_score(
    query: str,
    chunk_text: str,
    *,
    intent: IntentResult | None,
    rules: Mapping[str, Any] | None = None,
) -> float:
    rules = rules or load_intent_rules()
    facet_code = (intent.facet or intent.policy_code or "") if intent else ""
    keywords = _facet_keywords(facet_code, rules) if facet_code.startswith("A") else []

    if not keywords:
        # Fallback: any facet keyword present in query and chunk
        all_kws: list[str] = []
        for code, facet in (rules.get("factual_facets") or {}).items():
            if str(code).startswith("A"):
                all_kws.extend(_facet_keywords(str(code), rules))
        keywords = all_kws

    if not keywords:
        return 0.0

    q = query.lower()
    text = chunk_text.lower()
    hits = 0
    for kw in keywords:
        if kw in q and kw in text:
            hits += 1
    return min(1.0, hits / max(1, min(3, len([k for k in keywords if k in q]))))


def scheme_match_boost(
    candidate: RetrievalCandidate,
    resolution: SchemeResolution | None,
    *,
    min_confidence: float = 0.82,
) -> float:
    if resolution is None or not resolution.is_resolved:
        return 0.0
    if resolution.confidence < min_confidence:
        return 0.0
    target = resolution.scheme or resolution.resolved_scheme
    return 1.0 if candidate.scheme == target else 0.0


def parse_effective_date(value: str) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def freshness_sort_key(effective_date: str) -> float:
    dt = parse_effective_date(effective_date)
    return dt.timestamp() if dt else 0.0
