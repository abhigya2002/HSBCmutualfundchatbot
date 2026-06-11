"""Tests for Phase 2.3 extraction heuristics."""

from __future__ import annotations

import unittest
from pathlib import Path

from phase_2_3.extract import EXTRACT_VERSION, extract_main_fragment


class TestExtract(unittest.TestCase):
    def test_minimal_fixture_prefers_root(self):
        p = Path(__file__).resolve().parent / "fixtures" / "minimal_mf.html"
        raw = p.read_bytes()
        out = extract_main_fragment(raw)
        self.assertEqual(out.selector_used, "#root")
        self.assertIn("Expense ratio", out.main_html)
        self.assertEqual(out.extract_status, "partial")  # short text vs ok thresholds

    def test_extract_version(self):
        self.assertTrue(EXTRACT_VERSION.startswith("2.3"))


if __name__ == "__main__":
    unittest.main()
