"""Tests for Phase 4.6 end-to-end retrieval service."""

from __future__ import annotations

import unittest

from phase_4_1.config_load import phase4_retrieval_root
from phase_4_4.allowlist_filter import is_allowlisted_source
from phase_4_6.contracts import RetrievalRequest
from phase_4_6.evaluate import run_full_evaluation
from phase_4_6.handoff import build_phase5_handoff
from phase_4_6.service import RetrievalService, retrieve


class TestRetrievalServiceRefusal(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.service = RetrievalService()
        except RuntimeError:
            self.skipTest("indexes unavailable")

    def test_advisory_refuses_without_hybrid(self) -> None:
        outcome = self.service.retrieve("Should I buy HSBC Gilt Fund?")
        self.assertEqual(outcome.outcome_type, "refusal")
        self.assertTrue(outcome.hybrid_skipped)
        self.assertIsNotNone(outcome.refusal)
        self.assertTrue(is_allowlisted_source(outcome.refusal.citation_url))

    def test_comparison_refuses(self) -> None:
        outcome = self.service.retrieve("Compare HSBC Midcap and HSBC Small Cap")
        self.assertEqual(outcome.outcome_type, "refusal")
        self.assertTrue(outcome.hybrid_skipped)

    def test_icici_out_of_scope(self) -> None:
        outcome = self.service.retrieve("expense ratio ICICI Bluechip")
        self.assertEqual(outcome.outcome_type, "refusal")
        self.assertEqual(outcome.refusal.refusal_type, "out_of_scope")


class TestRetrievalServiceFactual(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.service = RetrievalService()
        except RuntimeError:
            self.skipTest("indexes unavailable")

    def test_factual_retrieval(self) -> None:
        outcome = self.service.retrieve("expense ratio HSBC Gilt Fund Direct Growth")
        self.assertEqual(outcome.outcome_type, "retrieval")
        self.assertFalse(outcome.hybrid_skipped)
        self.assertIsNotNone(outcome.retrieval)
        self.assertTrue(is_allowlisted_source(outcome.retrieval.citation_url))

    def test_performance_limited_flag(self) -> None:
        outcome = self.service.retrieve("HSBC Focused Fund past performance chart")
        self.assertEqual(outcome.outcome_type, "retrieval")
        self.assertTrue(outcome.performance_limited)

    def test_retrieve_helper(self) -> None:
        outcome = retrieve("exit load HSBC Midcap Fund")
        self.assertIn(outcome.outcome_type, ("retrieval", "refusal"))


class TestPhase5Handoff(unittest.TestCase):
    def test_handoff_shape(self) -> None:
        doc = build_phase5_handoff(
            index_version="idx_test",
            embedding_model_id="hash-embedding-v1",
            eval_summary={"passed": True},
        )
        self.assertEqual(doc["phase"], "4.6")
        self.assertIn("evidence_fields_for_phase5", doc)
        self.assertIn("refusal_contract", doc)


class TestFullEvaluation(unittest.TestCase):
    def test_eval_full_passes(self) -> None:
        try:
            service = RetrievalService()
        except RuntimeError:
            self.skipTest("indexes unavailable")
        report = run_full_evaluation(service)
        self.assertEqual(report["factual"].get("allowlist_violations"), 0)
        self.assertEqual(report["adversarial"].get("allowlist_violations"), 0)
        self.assertTrue(report["passed"], report)


class TestRetrievalRequest(unittest.TestCase):
    def test_request_contract(self) -> None:
        req = RetrievalRequest(query="test", session_id="s1")
        self.assertEqual(req.to_dict()["session_id"], "s1")


if __name__ == "__main__":
    unittest.main()
