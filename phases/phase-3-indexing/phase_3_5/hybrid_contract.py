"""Hybrid retrieval contract for Phase 4 (P3-12, P3-07)."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from phase_3_5 import PHASE_3_5_VERSION


def build_hybrid_contract(
    *,
    index_version: str,
    vector_active: dict[str, Any],
    keyword_index_dir: str,
    keyword_manifest: dict[str, Any],
    chunk_count: int,
) -> dict[str, Any]:
    """
    Document merge fields and fallback rules shared by vector + keyword channels.

    P3-12: keyword channel may return zero hits for stopword-only queries; Phase 4
    must still run vector retrieval (``keyword_empty_fallback``).

    P3-07: scheme aliases are query-side only — not stored in the index.
    """
    return {
        "phase": "3.5",
        "phase_3_5_version": PHASE_3_5_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_version": index_version,
        "shared_merge_keys": ["chunk_id", "source_url", "scheme"],
        "optional_merge_keys": ["section_title", "effective_date", "compliance_rank"],
        "vector_channel": {
            "active_pointer": "phase-3-chunking/artifacts/indexes/vector/active.json",
            "index_version": vector_active.get("index_version"),
            "embedding_model_id": vector_active.get("embedding_model_id"),
            "vector_index_dir": vector_active.get("vector_index_dir"),
        },
        "keyword_channel": {
            "active_pointer": "phase-3-indexing/artifacts/indexes/keyword/active.json",
            "index_version": index_version,
            "keyword_index_dir": keyword_index_dir,
            "algorithm": "bm25",
            "manifest": keyword_manifest,
        },
        "hybrid_policy": {
            "merge_strategy": "union_by_chunk_id",
            "score_normalization": "per_channel_minmax",
            "keyword_empty_fallback": "vector",
            "stopword_only_query_use_vector": True,
            "scheme_aliases": "query_side_only",
            "citation_allowlist": "phase-1 source_registry 16 Groww URLs",
        },
        "chunk_count": chunk_count,
    }
