"""Tests for Phase 2.5 doc_metadata assembly and candidate extractors."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from phase_2_5.candidates import extract_all_candidates, extract_expense_ratio
from phase_2_5.doc_metadata import METADATA_BUILDER_VERSION, build_doc_metadata


class TestCandidates(unittest.TestCase):
    def test_expense_ratio_groww_style(self):
        text = "Foo Expense ratio0.48% Rating bar"
        hit = extract_expense_ratio(text)
        self.assertIsNotNone(hit)
        self.assertIn("0.48%", hit.get("value_text", ""))

    def test_candidates_keys_present(self):
        text = """
        ## Overview
        Expense ratio 1.2%
        Min. for SIP ₹500
        Fund benchmark NIFTY 50 TRI
        ### Exit load, stamp duty and tax
        Nil for this plan
        ### Tax implication
        Returns are taxed as per your Income Tax slab.
        rated Moderate risk
        ELSS plans have a 3 year lock-in for tax saving under section 80C.
        """
        c = extract_all_candidates(text)
        self.assertIsNotNone(c["expense_ratio"])
        self.assertIsNotNone(c["min_sip"])
        self.assertIsNotNone(c["benchmark"])
        self.assertIsNotNone(c["exit_load"])
        self.assertIsNotNone(c["statement_tax"])
        self.assertIsNotNone(c["riskometer"])
        self.assertIsNotNone(c["lock_in"])


class TestDocMetadata(unittest.TestCase):
    def test_version(self):
        self.assertTrue(METADATA_BUILDER_VERSION.startswith("2.5"))

    def test_build_writes_sha_and_registry(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            md = t / "x.md"
            md.write_text("hello corpus\nExpense ratio 2.00%\n", encoding="utf-8")
            out = t / "meta.json"
            rec = build_doc_metadata(
                scheme="test-scheme",
                source_url="https://groww.in/mutual-funds/test-scheme",
                clean_md_path=md,
                raw_html_path=t / "r.html",
                crawl_path=t / "c.json",
                extract_path=t / "e.json",
                normalize_path=t / "n.json",
                metadata_out_path=out,
                registry_entry={"id": 1, "scheme": "test-scheme"},
            )
            self.assertTrue(out.is_file())
            self.assertEqual(rec["registry"]["id"], 1)
            self.assertIsNotNone(rec["content_sha256"])
            self.assertIsNotNone(rec["candidates"]["expense_ratio"])


if __name__ == "__main__":
    unittest.main()
