"""Tests for Phase 4.5 re-ranking and citation selection."""

from __future__ import annotations

import unittest

from phase_4_1.config_load import phase4_retrieval_root
from phase_4_2.contracts import IntentResult
from phase_4_3.contracts import SchemeResolution, SchemeStatus
from phase_4_4.allowlist_filter import is_allowlisted_source
from phase_4_4.contracts import CandidateScores, HybridRetrievalResult, RetrievalCandidate
from phase_4_5.citation import pick_citation_url
from phase_4_5.config_load import load_rerank_config
from phase_4_5.reranker import Reranker
from phase_4_5.signals import facet_match_score, lexical_overlap


GILT_URL = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"
MIDCAP_URL = "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth"


class TestSignals(unittest.TestCase):
    def test_lexical_overlap(self) -> None:
        score = lexical_overlap("expense ratio HSBC Gilt", "Expense ratio 0.48% for gilt fund")
        self.assertGreater(score, 0.0)

    def test_facet_match_expense_ratio(self) -> None:
        intent = IntentResult(
            intent="factual",
            action="retrieve",
            confidence=0.9,
            facet="A1",
            policy_code="A1",
        )
        score = facet_match_score(
            "expense ratio HSBC Gilt",
            "Total expense ratio is 0.48 percent",
            intent=intent,
        )
        self.assertGreaterEqual(score, 0.5)


class TestCitationPolicy(unittest.TestCase):
    def test_resolver_precedence_over_chunk(self) -> None:
        cfg = load_rerank_config()
        chunk = RetrievalCandidate(
            chunk_id="c1",
            text="text",
            source_url=MIDCAP_URL,
            scheme="hsbc-midcap-fund-direct-growth",
            scores=CandidateScores(),
        )
        resolution = SchemeResolution(
            scheme="hsbc-gilt-fund-direct-growth",
            source_url=GILT_URL,
            confidence=0.95,
            status=SchemeStatus.RESOLVED.value,
            citation_url_candidate=GILT_URL,
        )
        url, prec = pick_citation_url(chunk=chunk, resolution=resolution, config=cfg)
        self.assertEqual(url, GILT_URL)
        self.assertEqual(prec, "resolver_scheme")

    def test_chunk_url_when_no_resolver(self) -> None:
        cfg = load_rerank_config()
        chunk = RetrievalCandidate(
            chunk_id="c1",
            text="text",
            source_url=GILT_URL,
            scheme="hsbc-gilt-fund-direct-growth",
            scores=CandidateScores(),
        )
        url, prec = pick_citation_url(chunk=chunk, resolution=None, config=cfg)
        self.assertEqual(url, GILT_URL)
        self.assertEqual(prec, "chunk_source_url")


class TestRerankerUnit(unittest.TestCase):
    def test_picks_higher_facet_candidate(self) -> None:
        cfg = load_rerank_config()
        cfg["min_final_score"] = 0.01
        reranker = Reranker(cfg)
        hybrid = HybridRetrievalResult(
            query="expense ratio HSBC Gilt Fund",
            candidates=[
                RetrievalCandidate(
                    chunk_id="low",
                    text="general fund overview",
                    source_url=GILT_URL,
                    scheme="hsbc-gilt-fund-direct-growth",
                    scores=CandidateScores(vector=0.9, keyword=0.1, fused=0.9),
                ),
                RetrievalCandidate(
                    chunk_id="high",
                    text="Expense ratio 0.48 percent TER details",
                    source_url=GILT_URL,
                    scheme="hsbc-gilt-fund-direct-growth",
                    scores=CandidateScores(vector=0.5, keyword=0.8, fused=0.8),
                ),
            ],
        )
        intent = IntentResult(
            intent="factual",
            action="retrieve",
            confidence=0.9,
            facet="A1",
            policy_code="A1",
        )
        resolution = SchemeResolution(
            scheme="hsbc-gilt-fund-direct-growth",
            source_url=GILT_URL,
            confidence=0.95,
            status=SchemeStatus.RESOLVED.value,
            citation_url_candidate=GILT_URL,
        )
        result = reranker.rerank(hybrid, intent=intent, scheme_resolution=resolution)
        self.assertEqual(result.status, "found")
        self.assertEqual(result.chunk_id, "high")
        self.assertEqual(result.citation_url, GILT_URL)

    def test_not_found_empty_pool(self) -> None:
        reranker = Reranker()
        hybrid = HybridRetrievalResult(query="test", candidates=[])
        result = reranker.rerank(hybrid)
        self.assertEqual(result.status, "not_found_in_sources")
        self.assertTrue(is_allowlisted_source(result.citation_url))


class TestRerankerIntegration(unittest.TestCase):
    def test_citation_benchmark(self) -> None:
        from phase_4_4.hybrid_retriever import HybridRetriever
        from phase_4_5.evaluate import run_citation_benchmark

        bench = (
            phase4_retrieval_root()
            / "../phase-3-indexing/benchmarks/retrieval_benchmark.json"
        ).resolve()
        if not bench.is_file():
            self.skipTest("benchmark missing")
        try:
            retriever = HybridRetriever()
        except RuntimeError:
            self.skipTest("indexes unavailable")
        report = run_citation_benchmark(retriever, Reranker(), bench)
        self.assertGreaterEqual(report["citation_accuracy"], 0.9, report)


if __name__ == "__main__":
    unittest.main()
