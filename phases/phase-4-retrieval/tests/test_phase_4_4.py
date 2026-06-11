"""Tests for Phase 4.4 hybrid retrieval."""

from __future__ import annotations

import unittest

from phase_4_1.config_load import load_config, phase4_retrieval_root
from phase_4_3.contracts import SchemeResolution, SchemeStatus
from phase_4_4.allowlist_filter import canonicalize_source_url, is_allowlisted_source
from phase_4_4.contracts import CandidateScores, RetrievalCandidate
from phase_4_4.hybrid_retriever import HybridRetriever, _interim_fused


class TestAllowlistFilter(unittest.TestCase):
    def test_gilt_url_allowlisted(self) -> None:
        url = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"
        self.assertTrue(is_allowlisted_source(url))
        self.assertEqual(canonicalize_source_url(url + "/"), canonicalize_source_url(url))


class TestFusionHelpers(unittest.TestCase):
    def test_interim_fused_max(self) -> None:
        self.assertEqual(_interim_fused(0.2, 0.8), 0.8)
        self.assertEqual(_interim_fused(0.5, None), 0.5)


class TestRetrievalCandidateContract(unittest.TestCase):
    def test_to_dict(self) -> None:
        c = RetrievalCandidate(
            chunk_id="c1",
            text="hello",
            source_url="https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
            scheme="hsbc-gilt-fund-direct-growth",
            scores=CandidateScores(vector=0.1, keyword=0.2, fused=0.2),
        )
        d = c.to_dict()
        self.assertIn("scores", d)
        self.assertEqual(d["scores"]["fused"], 0.2)


class TestHybridRetrieverIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        vector_active = (
            phase4_retrieval_root()
            / "../phase-3-chunking/artifacts/indexes/vector/active.json"
        ).resolve()
        if not vector_active.is_file():
            cls.retriever = None
            return
        try:
            cls.retriever = HybridRetriever()
        except RuntimeError:
            cls.retriever = None

    def setUp(self) -> None:
        if self.retriever is None:
            self.skipTest("Phase 3 indexes not available")

    def test_retrieve_gilt_expense_ratio(self) -> None:
        resolution = SchemeResolution(
            scheme="hsbc-gilt-fund-direct-growth",
            source_url="https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
            confidence=0.95,
            status=SchemeStatus.RESOLVED.value,
            citation_url_candidate="https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
        )
        result = self.retriever.retrieve(
            "What is the expense ratio of HSBC Gilt Fund Direct Growth?",
            scheme_resolution=resolution,
        )
        self.assertGreater(len(result.candidates), 0)
        top = result.candidates[0]
        self.assertTrue(is_allowlisted_source(top.source_url))
        self.assertEqual(top.scheme, "hsbc-gilt-fund-direct-growth")

    def test_all_candidates_allowlisted(self) -> None:
        result = self.retriever.retrieve("exit load HSBC Midcap Fund")
        for cand in result.candidates:
            self.assertTrue(is_allowlisted_source(cand.source_url))

    def test_scheme_filter_applied(self) -> None:
        resolution = SchemeResolution(
            scheme="hsbc-midcap-fund-direct-growth",
            source_url="https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth",
            confidence=0.95,
            status=SchemeStatus.RESOLVED.value,
        )
        result = self.retriever.retrieve("exit load", scheme_resolution=resolution)
        self.assertEqual(result.scheme_filter, "hsbc-midcap-fund-direct-growth")
        for cand in result.candidates:
            self.assertEqual(cand.scheme, "hsbc-midcap-fund-direct-growth")


class TestHybridBenchmark(unittest.TestCase):
    def test_phase3_retrieval_benchmark(self) -> None:
        from phase_4_4.evaluate import run_hybrid_benchmark

        bench = (
            phase4_retrieval_root()
            / "../phase-3-indexing/benchmarks/retrieval_benchmark.json"
        ).resolve()
        if not bench.is_file():
            self.skipTest("retrieval_benchmark.json missing")
        try:
            retriever = HybridRetriever()
        except RuntimeError:
            self.skipTest("indexes not available")
        report = run_hybrid_benchmark(retriever, bench, k=5)
        self.assertGreaterEqual(report["recall_at_k"], 0.85, report)


if __name__ == "__main__":
    unittest.main()
