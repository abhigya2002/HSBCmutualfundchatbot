"""Tests for Phase 5.6 generation service and evaluation."""

from __future__ import annotations

import unittest

from phase_5_1.registry_bridge import is_allowlisted_url
from phase_5_3.citation import count_markdown_links
from phase_5_3.composer import sentence_count
from phase_5_6.contracts import GenerationRequest
from phase_5_6.handoff import build_phase6_handoff, default_handoff_path
from phase_5_6.service import GenerationService


GILT_URL = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"
DEFAULT_URL = "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth"


def _outcome_dict(*, outcome_type: str, query: str, refusal=None, retrieval=None, hybrid_skipped=False) -> dict:
    data: dict = {
        "outcome_type": outcome_type,
        "query": query,
        "hybrid_skipped": hybrid_skipped,
        "performance_limited": False,
    }
    if refusal is not None:
        data["refusal"] = refusal
    if retrieval is not None:
        data["retrieval"] = retrieval
    return data


def _advisory_outcome(query: str = "Should I buy HSBC Gilt?") -> dict:
    return _outcome_dict(
        outcome_type="refusal",
        query=query,
        hybrid_skipped=True,
        refusal={
            "refusal_type": "advisory",
            "message_hint": "hint",
            "citation_url": GILT_URL,
        },
    )


def _factual_outcome(query: str = "expense ratio HSBC Gilt") -> dict:
    return _outcome_dict(
        outcome_type="retrieval",
        query=query,
        retrieval={
            "status": "found",
            "query": query,
            "chunk_id": "hsbc-gilt-fund-direct-growth_c0000",
            "chunk_text": "Expense ratio 0.48%",
            "citation_url": GILT_URL,
            "section_title": "Overview",
            "effective_date": "2026-05-13T17:37:53.697902+00:00",
            "scheme": "hsbc-gilt-fund-direct-growth",
        },
    )


def _abstain_outcome(query: str = "what is the expense ratio") -> dict:
    return _outcome_dict(
        outcome_type="retrieval",
        query=query,
        retrieval={
            "status": "not_found_in_sources",
            "query": query,
            "chunk_id": "",
            "chunk_text": "",
            "citation_url": DEFAULT_URL,
            "section_title": "",
            "effective_date": "",
            "scheme": "",
            "not_found_reason": "below_min_final_score",
        },
    )


class TestGenerationServiceUnit(unittest.TestCase):
    def test_advisory_returns_refusal(self) -> None:
        service = GenerationService(retrieve_fn=lambda q, session_id="": _advisory_outcome(q))
        envelope = service.answer(GenerationRequest(query="Should I buy HSBC Gilt?"))
        self.assertEqual(envelope.outcome_type, "refusal")
        self.assertTrue(envelope.validation_passed)
        self.assertTrue(is_allowlisted_url(envelope.assistant["citation_url"]))

    def test_factual_returns_validated_answer(self) -> None:
        service = GenerationService(retrieve_fn=lambda q, session_id="": _factual_outcome(q))
        envelope = service.answer("expense ratio HSBC Gilt")
        self.assertEqual(envelope.outcome_type, "factual")
        self.assertTrue(envelope.validation_passed)
        self.assertIn("0.48%", envelope.assistant["body_text"])
        self.assertIn("Last updated from sources:", envelope.assistant["footer_line"])

    def test_abstain_path(self) -> None:
        service = GenerationService(retrieve_fn=lambda q, session_id="": _abstain_outcome(q))
        envelope = service.answer("what is the expense ratio")
        self.assertEqual(envelope.outcome_type, "abstention")
        self.assertTrue(envelope.validation_passed)

    def test_response_shape(self) -> None:
        service = GenerationService(retrieve_fn=lambda q, session_id="": _factual_outcome(q))
        envelope = service.answer("expense ratio")
        data = envelope.to_dict()
        for key in ("outcome_type", "assistant", "display_text", "validation_passed", "compliance_decision"):
            self.assertIn(key, data)
        self.assertEqual(count_markdown_links(envelope.assistant["citation_markdown"]), 1)
        self.assertLessEqual(sentence_count(envelope.assistant["body_text"]), 3)


class TestPhase6Handoff(unittest.TestCase):
    def test_handoff_shape(self) -> None:
        doc = build_phase6_handoff(eval_summary={"passed": True})
        self.assertEqual(doc["phase"], "5.6")
        self.assertIn("api_surface", doc)
        self.assertIn("middleware_hooks", doc)
        self.assertIn("pre_generation", doc["middleware_hooks"])
        self.assertIn("post_generation", doc["middleware_hooks"])

    def test_handoff_path_under_artifacts(self) -> None:
        path = default_handoff_path()
        self.assertTrue(str(path).endswith("phase6_generation_handoff.json"))


class TestGenerationIntegration(unittest.TestCase):
    def setUp(self) -> None:
        try:
            self.service = GenerationService()
        except RuntimeError:
            self.skipTest("GenerationService init failed")

    def test_live_advisory_refusal(self) -> None:
        try:
            envelope = self.service.answer("Should I buy HSBC Gilt Fund?")
        except RuntimeError:
            self.skipTest("Phase 4 indexes unavailable")
        self.assertEqual(envelope.outcome_type, "refusal")
        self.assertNotEqual(envelope.assistant.get("answer_type"), "factual")
        self.assertTrue(envelope.validation_passed)

    def test_live_factual_query(self) -> None:
        try:
            envelope = self.service.answer("expense ratio HSBC Gilt Fund Direct Growth")
        except RuntimeError:
            self.skipTest("Phase 4 indexes unavailable")
        self.assertIn(envelope.outcome_type, ("factual", "abstention"))
        self.assertTrue(envelope.validation_passed)
        self.assertTrue(is_allowlisted_url(envelope.assistant["citation_url"]))


class TestFullEvaluation(unittest.TestCase):
    def test_eval_full_runs(self) -> None:
        try:
            service = GenerationService()
        except RuntimeError:
            self.skipTest("GenerationService init failed")
        try:
            from phase_5_6.evaluate import run_full_evaluation

            report = run_full_evaluation(service)
        except RuntimeError:
            self.skipTest("Phase 4 indexes unavailable")
        self.assertIn("metrics", report)
        self.assertIn("redteam", report)
        self.assertEqual(report["metrics"]["allowlist_violation_count"], 0)


if __name__ == "__main__":
    unittest.main()
