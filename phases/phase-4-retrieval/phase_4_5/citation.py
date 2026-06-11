"""Citation URL selection with resolver precedence (P4-06)."""

from __future__ import annotations

from typing import Any, Mapping

from phase_4_3.contracts import SchemeResolution
from phase_4_4.allowlist_filter import canonicalize_source_url, is_allowlisted_source
from phase_4_4.contracts import RetrievalCandidate


def default_citation_url(config: Mapping[str, Any]) -> str:
    return str(
        config.get("default_citation_url")
        or "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth",
    )


def pick_citation_url(
    *,
    chunk: RetrievalCandidate | None,
    resolution: SchemeResolution | None,
    config: Mapping[str, Any],
) -> tuple[str, str]:
    """
    Return (citation_url, precedence_reason).

    P4-06: prefer resolver scheme URL when confident; else chunk URL; else default.
    """
    policy = config.get("citation_policy") or {}
    precedence = str(policy.get("precedence") or "resolver_scheme_over_chunk_url")
    default = default_citation_url(config)
    min_conf = float(config.get("scheme_match_min_confidence") or 0.82)

    if (
        precedence == "resolver_scheme_over_chunk_url"
        and resolution
        and resolution.is_resolved
        and resolution.confidence >= min_conf
    ):
        url = resolution.citation_url_candidate or resolution.source_url
        if url:
            canon = canonicalize_source_url(url)
            if is_allowlisted_source(canon):
                return canon, "resolver_scheme"

    if chunk and chunk.source_url:
        canon = canonicalize_source_url(chunk.source_url)
        if is_allowlisted_source(canon):
            return canon, "chunk_source_url"

    return canonicalize_source_url(default), "default_url"
