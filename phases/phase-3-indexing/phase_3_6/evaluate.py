"""Baseline retrieval benchmark evaluation."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from phase_3_6.benchmarks import BenchmarkQuery, load_benchmark
from phase_3_6.hybrid_search import _chunking_root, _ensure_chunking_path, hybrid_search, load_hybrid_indexes


@dataclass
class QueryEvalResult:
    benchmark_id: str
    query: str
    intent: str
    scheme: str
    expected_source_url: str
    hit: bool
    hit_rank: int | None
    top_chunk_ids: list[str]
    top_source_urls: list[str]


@dataclass
class BenchmarkReport:
    recall_at_k: float
    k: int
    threshold: float
    passed: bool
    query_count: int
    hit_count: int
    per_query: list[QueryEvalResult]

    def to_dict(self) -> dict[str, Any]:
        return {
            "recall_at_k": self.recall_at_k,
            "k": self.k,
            "threshold": self.threshold,
            "passed": self.passed,
            "query_count": self.query_count,
            "hit_count": self.hit_count,
            "per_query": [
                {
                    "benchmark_id": r.benchmark_id,
                    "query": r.query,
                    "intent": r.intent,
                    "scheme": r.scheme,
                    "expected_source_url": r.expected_source_url,
                    "hit": r.hit,
                    "hit_rank": r.hit_rank,
                    "top_chunk_ids": r.top_chunk_ids,
                    "top_source_urls": r.top_source_urls,
                }
                for r in self.per_query
            ],
        }


def _normalize_url(url: str) -> str:
    u = url.strip().rstrip("/")
    if u.startswith("https://www."):
        u = "https://" + u[12:]
    return u.lower()


def _is_hit(
    hits: list,
    expected_url: str,
    expected_chunk_id: str | None,
) -> tuple[bool, int | None]:
    canon_expected = _normalize_url(expected_url)
    for rank, hit in enumerate(hits, start=1):
        url_ok = _normalize_url(hit.source_url) == canon_expected
        chunk_ok = expected_chunk_id is None or hit.chunk_id == expected_chunk_id
        if url_ok and chunk_ok:
            return True, rank
    return False, None


def run_benchmark_evaluation(
    indexing_root: Path,
    config: Mapping[str, Any],
    *,
    benchmark_path: Path | None = None,
) -> BenchmarkReport:
    cfg = config.get("phase3_6") or {}
    k = int(cfg.get("recall_at_k", 5))
    threshold = float(cfg.get("recall_threshold", 0.6))

    queries = load_benchmark(benchmark_path)
    _ensure_chunking_path(indexing_root)
    vector_index, keyword_index, _, _ = load_hybrid_indexes(indexing_root)

    from phase_3_4.providers.base import get_provider

    chunking_config_path = _chunking_root(indexing_root) / "config" / "chunking.defaults.json"
    chunking_config = json.loads(chunking_config_path.read_text(encoding="utf-8"))
    provider = get_provider(chunking_config)

    results: list[QueryEvalResult] = []
    hits_n = 0

    for bq in queries:
        retrieved = hybrid_search(
            bq.query,
            vector_index=vector_index,
            keyword_index=keyword_index,
            embedding_provider=provider,
            top_k=k,
            scheme=bq.scheme or None,
        )
        hit, rank = _is_hit(retrieved, bq.expected_source_url, bq.expected_chunk_id)
        if hit:
            hits_n += 1
        results.append(
            QueryEvalResult(
                benchmark_id=bq.id,
                query=bq.query,
                intent=bq.intent,
                scheme=bq.scheme,
                expected_source_url=bq.expected_source_url,
                hit=hit,
                hit_rank=rank,
                top_chunk_ids=[h.chunk_id for h in retrieved],
                top_source_urls=[h.source_url for h in retrieved],
            ),
        )

    recall = hits_n / len(queries) if queries else 0.0
    return BenchmarkReport(
        recall_at_k=recall,
        k=k,
        threshold=threshold,
        passed=recall >= threshold,
        query_count=len(queries),
        hit_count=hits_n,
        per_query=results,
    )
