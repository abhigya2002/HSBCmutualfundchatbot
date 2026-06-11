"""Benchmark evaluation for Phase 4.4 hybrid retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase_4_3.contracts import SchemeResolution
from phase_4_4.hybrid_retriever import HybridRetriever


@dataclass
class HybridQueryEval:
    benchmark_id: str
    query: str
    expected_source_url: str
    expected_scheme: str
    hit: bool
    hit_rank: int | None
    top_source_urls: list[str]


def _normalize_url(url: str) -> str:
    u = url.strip().rstrip("/").lower()
    if u.startswith("https://www."):
        u = "https://" + u[12:]
    return u


def run_hybrid_benchmark(
    retriever: HybridRetriever,
    bench_path: Path,
    *,
    k: int = 5,
    recall_threshold: float = 0.85,
) -> dict[str, Any]:
    data = json.loads(bench_path.read_text(encoding="utf-8"))
    queries = data.get("queries") or []
    per_query: list[HybridQueryEval] = []
    hits = 0

    for row in queries:
        q = str(row.get("query") or "")
        expected_url = str(row.get("expected_source_url") or "")
        expected_scheme = str(row.get("scheme") or "")
        resolution = SchemeResolution(
            scheme=expected_scheme,
            source_url=expected_url,
            confidence=0.95,
            status="resolved",
            citation_url_candidate=expected_url,
        )
        result = retriever.retrieve(q, scheme_resolution=resolution)
        canon_expected = _normalize_url(expected_url)
        hit = False
        hit_rank = None
        top_urls: list[str] = []
        for rank, cand in enumerate(result.candidates[:k], start=1):
            url = _normalize_url(cand.source_url)
            top_urls.append(url)
            if url == canon_expected and not hit:
                hit = True
                hit_rank = rank
        if hit:
            hits += 1
        per_query.append(
            HybridQueryEval(
                benchmark_id=str(row.get("id") or ""),
                query=q,
                expected_source_url=expected_url,
                expected_scheme=expected_scheme,
                hit=hit,
                hit_rank=hit_rank,
                top_source_urls=top_urls,
            ),
        )

    total = len(per_query)
    recall = hits / total if total else 0.0
    return {
        "k": k,
        "recall_at_k": round(recall, 4),
        "threshold": recall_threshold,
        "passed": recall >= recall_threshold,
        "query_count": total,
        "hit_count": hits,
        "per_query": [
            {
                "benchmark_id": r.benchmark_id,
                "query": r.query,
                "expected_source_url": r.expected_source_url,
                "expected_scheme": r.expected_scheme,
                "hit": r.hit,
                "hit_rank": r.hit_rank,
                "top_source_urls": r.top_source_urls,
            }
            for r in per_query
        ],
    }
