"""Tests for Phase 5.5 post-generation validators and repair."""

from __future__ import annotations

import unittest

from phase_5_1.config_load import load_config, phase5_guardrails_root
from phase_5_1.handoff import load_prohibited_phrases
from phase_5_2.engine import PreGenerationComplianceEngine
from phase_5_3.composer import RefusalComposer
from phase_5_4.composer import FactualComposer
from phase_5_5.contracts import DraftEnvelope
from phase_5_5.links import normalize_url_text, validate_citation_url
from phase_5_5.prohibited import find_prohibited_phrases, strip_quoted_echo
from phase_5_5.run_validate import run_benchmark
from phase_5_5.sentence import count_sentences, truncate_to_sentence_budget
from phase_5_5.validator import PostGenerationValidator


GILT_URL = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"
DEFAULT_URL = "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth"
CITATION_MD = "[HSBC Gilt Fund (Direct Growth)](https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth)"
DISCLAIMER = "Facts-only. No investment advice."


def _refusal_draft(**overrides) -> dict:
    base = {
        "answer_type": "refusal",
        "refusal_type": "advisory",
        "body_text": "I cannot provide investment advice or personal recommendations.",
        "citation_url": GILT_URL,
        "citation_markdown": CITATION_MD,
        "disclaimer_line": DISCLAIMER,
    }
    base.update(overrides)
    return base


def _factual_draft(**overrides) -> dict:
    base = {
        "answer_type": "factual",
        "body_text": "The expense ratio is 0.48%.",
        "citation_url": GILT_URL,
        "citation_markdown": CITATION_MD,
        "footer_line": "Last updated from sources: 13 May 2026",
        "footer_date": "13 May 2026",
        "evidence_chunk_id": "hsbc-gilt-fund-direct-growth_c0000",
        "disclaimer_line": DISCLAIMER,
    }
    base.update(overrides)
    return base


class TestSentenceTokenizer(unittest.TestCase):
    def test_semicolon_clauses_counted(self) -> None:
        text = "A; B; C; D"
        self.assertEqual(count_sentences(text, count_semicolon_clauses=True), 4)

    def test_truncate_semicolon_clauses(self) -> None:
        text = "A; B; C; D"
        truncated = truncate_to_sentence_budget(text, 3, count_semicolon_clauses=True)
        self.assertEqual(count_sentences(truncated, count_semicolon_clauses=True), 3)


class TestLinks(unittest.TestCase):
    def test_normalize_groww_without_scheme(self) -> None:
        normalized = normalize_url_text("groww.in/mutual-funds/hsbc-gilt-fund-direct-growth")
        ok, canon, _ = validate_citation_url(normalized)
        self.assertTrue(ok)
        self.assertEqual(canon, GILT_URL)


class TestProhibited(unittest.TestCase):
    def test_quoted_echo_not_flagged(self) -> None:
        cfg = load_config()
        prohibited, _ = load_prohibited_phrases(cfg)
        assert prohibited is not None
        text = 'I cannot answer "should I buy HSBC Gilt Fund" with advice.'
        self.assertEqual(find_prohibited_phrases(text, prohibited), [])
        self.assertNotIn("should i buy", strip_quoted_echo(text).lower())


class TestValidator(unittest.TestCase):
    def setUp(self) -> None:
        self.validator = PostGenerationValidator()

    def test_valid_refusal_passes(self) -> None:
        result = self.validator.validate(_refusal_draft())
        self.assertTrue(result.passed)
        self.assertFalse(result.repaired)

    def test_valid_factual_passes(self) -> None:
        result = self.validator.validate(_factual_draft())
        self.assertTrue(result.passed)

    def test_double_link_fails_without_repair(self) -> None:
        draft = _factual_draft(
            citation_markdown=(
                "[A](https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth) "
                "[B](https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth)"
            ),
        )
        result = self.validator.validate(draft)
        self.assertFalse(result.passed)
        self.assertTrue(any(v.code == "citation_link_count" for v in result.violations))

    def test_double_link_repaired(self) -> None:
        draft = _factual_draft(
            citation_markdown=(
                "[A](https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth) "
                "[B](https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth)"
            ),
        )
        result = self.validator.validate_and_repair(draft)
        self.assertTrue(result.passed)
        self.assertTrue(result.repaired)

    def test_sentence_budget_repaired(self) -> None:
        draft = _refusal_draft(body_text="One; Two; Three; Four")
        result = self.validator.validate_and_repair(draft)
        self.assertTrue(result.passed)
        self.assertTrue(result.repaired)

    def test_prohibited_phrase_fallback_refusal(self) -> None:
        draft = _factual_draft(body_text="You should buy this fund because it is a good investment.")
        result = self.validator.validate_and_repair(draft)
        self.assertTrue(result.passed)
        self.assertEqual(result.answer_type, "refusal")
        self.assertTrue(result.repaired)

    def test_missing_footer_repaired(self) -> None:
        draft = _factual_draft(footer_line="", footer_date="")
        result = self.validator.validate_and_repair(draft)
        self.assertTrue(result.passed)
        self.assertIn("date unavailable", result.draft.get("footer_line", ""))


class TestComposerIntegration(unittest.TestCase):
    def test_refusal_compose_then_validate(self) -> None:
        refusal = RefusalComposer().compose(
            {
                "refusal_type": "advisory",
                "message_hint": "hint",
                "citation_url": GILT_URL,
            },
        )
        result = PostGenerationValidator().validate(refusal)
        self.assertTrue(result.passed)

    def test_factual_compose_then_validate(self) -> None:
        factual = FactualComposer().compose(
            {
                "status": "found",
                "query": "expense ratio HSBC Gilt",
                "chunk_id": "hsbc-gilt-fund-direct-growth_c0000",
                "chunk_text": "Expense ratio 0.48%",
                "citation_url": GILT_URL,
                "section_title": "Overview",
                "effective_date": "2026-05-13T17:37:53.697902+00:00",
                "scheme": "hsbc-gilt-fund-direct-growth",
            },
        )
        result = PostGenerationValidator().validate(factual)
        self.assertTrue(result.passed)


class TestValidationBenchmark(unittest.TestCase):
    def test_benchmark_all_pass(self) -> None:
        bench = phase5_guardrails_root() / "benchmarks" / "validation_benchmark.json"
        self.assertTrue(bench.is_file())
        report = run_benchmark(PostGenerationValidator(), bench)
        self.assertEqual(report["cases_total"], 8)
        self.assertTrue(report["passed"], report["results"])


class TestLivePipeline(unittest.TestCase):
    def test_live_query_compose_validate(self) -> None:
        try:
            from phase_5_2.phase4_bridge import retrieve_outcome
        except ImportError:
            self.skipTest("phase4 bridge unavailable")
        try:
            outcome = retrieve_outcome("expense ratio HSBC Gilt Fund Direct Growth")
        except RuntimeError:
            self.skipTest("Phase 4 indexes unavailable")

        compliance = PreGenerationComplianceEngine().evaluate(outcome)
        validator = PostGenerationValidator()
        if compliance.decision == "refuse" and outcome.refusal is not None:
            draft = RefusalComposer().compose(outcome.refusal)
        elif compliance.decision == "allow_compose" and outcome.retrieval is not None:
            draft = FactualComposer().compose(
                outcome.retrieval,
                performance_limited=compliance.performance_limited,
            )
        else:
            self.skipTest("no composable outcome")
        result = validator.validate(draft)
        self.assertTrue(result.passed, [v.message for v in result.violations])


if __name__ == "__main__":
    unittest.main()
