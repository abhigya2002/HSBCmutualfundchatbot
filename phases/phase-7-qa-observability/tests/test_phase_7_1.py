"""Unit tests for Phase 7.1 metrics helpers."""

from __future__ import annotations

import unittest

from phase_7_1.allowlist import is_allowlisted, slug_from_url
from phase_7_1.format_checks import assess_format_compliance, sentence_count


class TestAllowlist(unittest.TestCase):
    def test_allowlisted_url(self) -> None:
        url = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"
        self.assertTrue(is_allowlisted(url))
        self.assertEqual(slug_from_url(url), "hsbc-gilt-fund-direct-growth")

    def test_rejects_external(self) -> None:
        self.assertFalse(is_allowlisted("https://example.com/fund"))


class TestFormatChecks(unittest.TestCase):
    def test_sentence_count(self) -> None:
        self.assertEqual(sentence_count("One. Two. Three."), 3)
        self.assertEqual(sentence_count("Single sentence"), 1)

    def test_factual_compliant_envelope(self) -> None:
        env = {
            "outcome_type": "factual",
            "validation_passed": True,
            "assistant": {
                "body_text": "The expense ratio is 0.48%.",
                "citation_url": "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
                "footer_line": "Last updated from sources: May 2026",
                "footer_date": "May 2026",
                "validation_passed": True,
            },
        }
        result = assess_format_compliance(env)
        self.assertTrue(result["compliant"])
        self.assertEqual(result["allowlist_violations"], 0)

    def test_refusal_not_format_compliant(self) -> None:
        env = {
            "outcome_type": "refusal",
            "validation_passed": True,
            "assistant": {
                "body_text": "I cannot advise.",
                "citation_url": "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
                "footer_line": "",
            },
        }
        result = assess_format_compliance(env)
        self.assertFalse(result["compliant"])


if __name__ == "__main__":
    unittest.main()
