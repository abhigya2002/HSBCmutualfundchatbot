"""Citation accuracy evaluation for Phase 4.5."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from phase_4_2.contracts import IntentResult
from phase_4_3.contracts import SchemeResolution
from phase_4_4.hybrid_retriever import HybridRetriever
from phase_4_5.reranker import Reranker


def _normalize_url(url: str) -> str:
    u = url.strip().rstrip("/").lower()
    if u.startswith("https://www."):
        u = "https://" + u[12:]
    return u


def run_citation_benchmark(
    retriever: HybridRetriever,
    reranker: Reranker,
    bench_path: Path,
    *,
    threshold: float = 0.9,
) -> dict[str, Any]:
    data = json.loads(bench_path.read_text(encoding="utf-8"))
    rows = data.get("queries") or []
    results = []
    hits = 0

    for row in rows:
        q = str(row.get("query") or "")
        expected_url = str(row.get("expected_source_url") or "")
        expected_scheme = str(row.get("scheme") or "")
        intent = IntentResult(
            intent="factual",
            action="retrieve",
            confidence=0.9,
            policy_code=str(row.get("intent") or "A1"),
            facet=str(row.get("intent") or "A1"),
        )
        resolution = SchemeResolution(
            scheme=expected_scheme,
            source_url=expected_url,
            confidence=0.95,
            status="resolved",
            citation_url_candidate=expected_url,
        )
        hybrid = retriever.retrieve(q, scheme_resolution=resolution)
        response = reranker.rerank(hybrid, intent=intent, scheme_resolution=resolution)
        got = _normalize_url(response.citation_url)
        expected = _normalize_url(expected_url)
        ok = response.status == "found" and got == expected
        if ok:
            hits += 1
        results.append(
            {
                "id": row.get("id"),
                "query": q,
                "expected_source_url": expected_url,
                "got_citation_url": response.citation_url,
                "status": response.status,
                "chunk_id": response.chunk_id,
                "final_score": response.scores.final_score,
                "citation_precedence": response.citation_precedence,
                "passed": ok,
            },
        )

    total = len(results)
    accuracy = hits / total if total else 0.0
    return {
        "citation_accuracy": round(accuracy, 4),
        "threshold": threshold,
        "passed": accuracy >= threshold,
        "query_count": total,
        "hit_count": hits,
        "results": results,
    }
