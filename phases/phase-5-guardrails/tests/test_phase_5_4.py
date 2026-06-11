"""Tests for Phase 5.4 factual response composer."""

from __future__ import annotations

import unittest

from phase_5_1.config_load import load_config, phase5_guardrails_root
from phase_5_1.registry_bridge import is_allowlisted_url
from phase_5_2.contracts import ComplianceDecision
from phase_5_2.engine import PreGenerationComplianceEngine
from phase_5_3.citation import count_markdown_links
from phase_5_3.composer import sentence_count
from phase_5_4.composer import FactualComposer, compose_factual
from phase_5_4.contracts import FactualAnswer
from phase_5_4.extractive import compose_body_sentences, detect_facet, load_factual_templates
from phase_5_4.footer import resolve_footer_date
from phase_5_4.numbers import audit_number_grounding, strip_uncited_numbers
from phase_5_4.retrieval_adapter import normalize_retrieval
from phase_5_4.run_compose import run_benchmark
from phase_5_1.handoff import load_composer_defaults


GILT_URL = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"
DEFAULT_URL = "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth"


def _retrieval(
    *,
    query: str,
    chunk_text: str,
    citation_url: str = GILT_URL,
    chunk_id: str = "test_chunk_001",
    effective_date: str = "2026-05-13T17:37:53.697902+00:00",
    section_title: str = "Fund overview",
    scheme: str = "hsbc-gilt-fund-direct-growth",
) -> dict:
    return {
        "status": "found",
        "query": query,
        "chunk_id": chunk_id,
        "chunk_text": chunk_text,
        "citation_url": citation_url,
        "section_title": section_title,
        "effective_date": effective_date,
        "scheme": scheme,
    }


class TestExtractive(unittest.TestCase):
    def test_detect_expense_ratio_facet(self) -> None:
        facet = detect_facet("expense ratio HSBC Gilt", "Expense ratio 0.48%")
        self.assertEqual(facet, "expense_ratio")

    def test_compose_expense_ratio_sentence(self) -> None:
        cfg = load_config()
        templates = load_factual_templates(cfg)
        sentences = compose_body_sentences(
            query="expense ratio HSBC Gilt",
            chunk_text="Expense ratio 0.48%",
            section_title="Overview",
            templates=templates,
        )
        self.assertIn("0.48%", " ".join(sentences))


class TestFooter(unittest.TestCase):
    def test_footer_uses_effective_date(self) -> None:
        cfg = load_config()
        composer, _ = load_composer_defaults(cfg)
        assert composer is not None
        footer_date, footer_line = resolve_footer_date("2026-05-13T17:37:53.697902+00:00", composer)
        self.assertIn("May 2026", footer_date)
        self.assertIn(footer_date, footer_line)

    def test_footer_unavailable_when_missing_date(self) -> None:
        cfg = load_config()
        composer, _ = load_composer_defaults(cfg)
        assert composer is not None
        footer_date, footer_line = resolve_footer_date("", composer)
        self.assertEqual(footer_date, composer.footer_date_unavailable)
        self.assertIn("date unavailable", footer_line)


class TestNumberGrounding(unittest.TestCase):
    def test_flags_uncited_number(self) -> None:
        flags = audit_number_grounding("The expense ratio is 0.99%.", "Expense ratio 0.48%")
        self.assertTrue(any(f.startswith("uncited_number:") for f in flags))

    def test_strip_uncited_numbers(self) -> None:
        cleaned, flags = strip_uncited_numbers("The expense ratio is 0.99%.", "Expense ratio 0.48%")
        self.assertTrue(flags)
        self.assertNotIn("0.99%", cleaned)


class TestFactualComposer(unittest.TestCase):
    def setUp(self) -> None:
        self.composer = FactualComposer()

    def test_compose_expense_ratio(self) -> None:
        answer = self.composer.compose(
            _retrieval(
                query="expense ratio HSBC Gilt Fund Direct Growth",
                chunk_text="Expense ratio 0.48%",
            ),
        )
        self.assertIn("0.48%", answer.body_text)
        self.assertEqual(answer.citation_url, GILT_URL)
        self.assertEqual(answer.evidence_chunk_id, "test_chunk_001")

    def test_single_citation_markdown(self) -> None:
        answer = self.composer.compose(_retrieval(query="exit load", chunk_text="Exit load Nil"))
        self.assertEqual(count_markdown_links(answer.citation_markdown), 1)
        self.assertEqual(count_markdown_links(answer.body_text), 0)

    def test_sentence_budget(self) -> None:
        answer = self.composer.compose(_retrieval(query="expense ratio", chunk_text="Expense ratio 0.48%"))
        self.assertLessEqual(sentence_count(answer.body_text), 3)

    def test_footer_and_disclaimer_present(self) -> None:
        answer = self.composer.compose(_retrieval(query="expense ratio", chunk_text="Expense ratio 0.48%"))
        self.assertIn("Last updated from sources:", answer.footer_line)
        self.assertIn("Facts-only", answer.disclaimer_line)

    def test_non_allowlisted_citation_falls_back(self) -> None:
        answer = self.composer.compose(
            _retrieval(query="expense ratio", chunk_text="Expense ratio 0.48%", citation_url="https://google.com"),
        )
        self.assertEqual(answer.citation_url, DEFAULT_URL)

    def test_performance_limited_clarifier(self) -> None:
        answer = self.composer.compose(
            _retrieval(query="past performance", chunk_text="Past performance +12.1%"),
            performance_limited=True,
        )
        self.assertTrue(answer.performance_limited)
        self.assertIn("projection", answer.body_text.lower())

    def test_compose_from_compliance(self) -> None:
        decision = ComplianceDecision(
            decision="allow_compose",
            reasons=["retrieval_evidence_present"],
            performance_limited=False,
            composer_route="factual",
            outcome_type="retrieval",
            query="expense ratio",
        )
        answer = self.composer.compose_from_compliance(
            decision,
            _retrieval(query="expense ratio", chunk_text="Expense ratio 0.48%"),
        )
        self.assertIsInstance(answer, FactualAnswer)

    def test_rejects_non_factual_compliance(self) -> None:
        decision = ComplianceDecision(
            decision="refuse",
            reasons=[],
            performance_limited=False,
            composer_route="refusal",
            outcome_type="refusal",
            query="Should I buy?",
        )
        with self.assertRaises(ValueError):
            self.composer.compose_from_compliance(decision, _retrieval(query="x", chunk_text="y"))

    def test_requires_found_status(self) -> None:
        with self.assertRaises(ValueError):
            self.composer.compose({"status": "not_found_in_sources", "chunk_text": ""})


class TestFactualBenchmark(unittest.TestCase):
    def test_benchmark_all_pass(self) -> None:
        bench = phase5_guardrails_root() / "benchmarks" / "factual_composer_benchmark.json"
        self.assertTrue(bench.is_file())
        report = run_benchmark(FactualComposer(), bench)
        self.assertEqual(report["cases_total"], 6)
        self.assertTrue(report["passed"], report["results"])


class TestFactualIntegration(unittest.TestCase):
    def test_live_factual_pipeline(self) -> None:
        try:
            from phase_5_2.phase4_bridge import retrieve_outcome
        except ImportError:
            self.skipTest("phase4 bridge unavailable")
        try:
            outcome = retrieve_outcome("expense ratio HSBC Gilt Fund Direct Growth")
        except RuntimeError:
            self.skipTest("Phase 4 indexes unavailable")

        compliance = PreGenerationComplianceEngine().evaluate(outcome)
        if compliance.decision != "allow_compose" or outcome.retrieval is None:
            self.skipTest("retrieval path unavailable for query")
        answer = compose_factual(outcome.retrieval, performance_limited=compliance.performance_limited)
        self.assertTrue(is_allowlisted_url(answer.citation_url))
        self.assertLessEqual(sentence_count(answer.body_text), 3)
        self.assertTrue(answer.evidence_chunk_id)


if __name__ == "__main__":
    unittest.main()
