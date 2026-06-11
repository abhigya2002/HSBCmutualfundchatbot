"""Tests for Phase 5.3 refusal response composer."""

from __future__ import annotations

import unittest

from phase_5_1.config_load import load_config, phase5_guardrails_root
from phase_5_1.registry_bridge import is_allowlisted_url
from phase_5_2.contracts import ComplianceDecision
from phase_5_2.engine import PreGenerationComplianceEngine
from phase_5_3 import REFUSAL_TYPES
from phase_5_3.citation import count_markdown_links, load_refusal_templates
from phase_5_3.composer import RefusalComposer, compose_refusal, sentence_count
from phase_5_3.contracts import RefusalAnswer
from phase_5_3.refusal_adapter import NormalizedRefusal, normalize_refusal
from phase_5_3.run_compose import run_benchmark


DEFAULT_URL = "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth"
GILT_URL = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"


def _refusal(
    refusal_type: str,
    *,
    citation_url: str = GILT_URL,
) -> dict:
    return {
        "refusal_type": refusal_type,
        "message_hint": "internal guidance only",
        "citation_url": citation_url,
    }


class TestRefusalTemplates(unittest.TestCase):
    def test_all_refusal_types_have_templates(self) -> None:
        cfg = load_config()
        template_set = load_refusal_templates(cfg)
        for rtype in REFUSAL_TYPES:
            body = template_set.templates.get(rtype, "")
            self.assertTrue(body.strip(), f"missing template for {rtype}")


class TestRefusalComposer(unittest.TestCase):
    def setUp(self) -> None:
        self.composer = RefusalComposer()

    def test_all_refusal_types_compose(self) -> None:
        for rtype in REFUSAL_TYPES:
            answer = self.composer.compose(_refusal(rtype))
            self.assertEqual(answer.refusal_type, rtype)
            self.assertTrue(answer.body_text.strip())
            self.assertIn("Facts-only", answer.disclaimer_line)

    def test_exactly_one_markdown_link(self) -> None:
        answer = self.composer.compose(_refusal("advisory"))
        self.assertEqual(count_markdown_links(answer.citation_markdown), 1)
        self.assertEqual(count_markdown_links(answer.body_text), 0)

    def test_citation_allowlisted(self) -> None:
        for rtype in REFUSAL_TYPES:
            answer = self.composer.compose(_refusal(rtype))
            self.assertTrue(is_allowlisted_url(answer.citation_url), answer.citation_url)

    def test_non_allowlisted_falls_back_to_default(self) -> None:
        answer = self.composer.compose(_refusal("advisory", citation_url="https://google.com"))
        self.assertEqual(answer.citation_url, DEFAULT_URL)

    def test_body_does_not_echo_message_hint(self) -> None:
        answer = self.composer.compose(_refusal("advisory"))
        self.assertNotIn("internal guidance only", answer.body_text)

    def test_sentence_budget_three_or_fewer(self) -> None:
        for rtype in REFUSAL_TYPES:
            answer = self.composer.compose(_refusal(rtype))
            self.assertLessEqual(sentence_count(answer.body_text), 3, rtype)

    def test_display_text_includes_all_parts(self) -> None:
        answer = self.composer.compose(_refusal("comparison"))
        display = answer.display_text
        self.assertIn(answer.body_text, display)
        self.assertIn(answer.citation_markdown, display)
        self.assertIn(answer.disclaimer_line, display)

    def test_compose_from_compliance(self) -> None:
        decision = ComplianceDecision(
            decision="refuse",
            reasons=["phase4_refusal_short_circuit"],
            performance_limited=False,
            composer_route="refusal",
            outcome_type="refusal",
            query="Should I buy?",
            refusal_type="advisory",
        )
        answer = self.composer.compose_from_compliance(decision, _refusal("advisory"))
        self.assertIsInstance(answer, RefusalAnswer)

    def test_compose_from_compliance_rejects_non_refusal(self) -> None:
        decision = ComplianceDecision(
            decision="allow_compose",
            reasons=[],
            performance_limited=False,
            composer_route="factual",
            outcome_type="retrieval",
            query="expense ratio",
        )
        with self.assertRaises(ValueError):
            self.composer.compose_from_compliance(decision, _refusal("advisory"))


class TestRefusalAdapter(unittest.TestCase):
    def test_normalize_dict(self) -> None:
        normalized = normalize_refusal(_refusal("disambiguate", citation_url=DEFAULT_URL))
        self.assertEqual(normalized.refusal_type, "disambiguate")
        self.assertEqual(normalized.citation_url, DEFAULT_URL)


class TestRefusalBenchmark(unittest.TestCase):
    def test_benchmark_all_pass(self) -> None:
        bench = phase5_guardrails_root() / "benchmarks" / "refusal_composer_benchmark.json"
        self.assertTrue(bench.is_file())
        report = run_benchmark(RefusalComposer(), bench)
        self.assertEqual(report["cases_total"], 8)
        self.assertTrue(report["passed"], report["results"])


class TestRefusalIntegration(unittest.TestCase):
    def test_live_advisory_pipeline(self) -> None:
        try:
            from phase_5_2.phase4_bridge import retrieve_outcome
        except ImportError:
            self.skipTest("phase4 bridge unavailable")
        try:
            outcome = retrieve_outcome("Should I buy HSBC Gilt Fund?")
        except RuntimeError:
            self.skipTest("Phase 4 indexes unavailable")

        compliance = PreGenerationComplianceEngine().evaluate(outcome)
        self.assertEqual(compliance.decision, "refuse")
        assert outcome.refusal is not None
        answer = compose_refusal(outcome.refusal)
        self.assertTrue(is_allowlisted_url(answer.citation_url))
        self.assertEqual(count_markdown_links(answer.citation_markdown), 1)


if __name__ == "__main__":
    unittest.main()
