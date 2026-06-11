"""Phase 4 retrieval handoff document."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from phase_3_6 import PHASE_3_6_VERSION


def build_phase4_handoff(
    *,
    index_version: str,
    chunking_root: Path,
    indexing_root: Path,
    index_manifest: dict[str, Any],
    benchmark_report: dict[str, Any],
    hybrid_contract_path: Path,
) -> dict[str, Any]:
    hybrid = {}
    if hybrid_contract_path.is_file():
        hybrid = json.loads(hybrid_contract_path.read_text(encoding="utf-8"))

    return {
        "phase": "3.6",
        "phase_3_6_version": PHASE_3_6_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_version": index_version,
        "index_manifest_summary": {
            "partial_corpus": index_manifest.get("partial_corpus"),
            "schemes_indexable": index_manifest.get("schemes_indexable"),
            "total_chunks": index_manifest.get("total_chunks"),
            "benchmark_passed": index_manifest.get("benchmark_passed"),
        },
        "paths": {
            "chunking_workspace": str(chunking_root),
            "indexing_workspace": str(indexing_root),
            "vector_active_pointer": "phase-3-chunking/artifacts/indexes/vector/active.json",
            "keyword_active_pointer": "phase-3-indexing/artifacts/indexes/keyword/active.json",
            "hybrid_contract": "phase-3-indexing/artifacts/hybrid_retrieval_contract.json",
            "retrieval_benchmark": "phase-3-indexing/benchmarks/retrieval_benchmark.json",
        },
        "hybrid_api_surface": {
            "search": "hybrid_search(query, top_k, scheme?, source_url?)",
            "merge_keys": hybrid.get("shared_merge_keys", ["chunk_id", "source_url", "scheme"]),
            "keyword_empty_fallback": hybrid.get("hybrid_policy", {}).get("keyword_empty_fallback", "vector"),
            "filter_rules": {
                "source_url": "must be one of 16 allowlisted Groww URLs (Phase 1 registry)",
                "no_off_corpus_urls": True,
            },
        },
        "version_pins": {
            "index_version": index_version,
            "embedding_model_id": index_manifest.get("embedding_model_id"),
        },
        "benchmark_summary": {
            "recall_at_k": benchmark_report.get("recall_at_k"),
            "k": benchmark_report.get("k"),
            "passed": benchmark_report.get("passed"),
        },
    }
