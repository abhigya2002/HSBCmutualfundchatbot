"""Tests for Phase 2.6 sections, quality gate, and clean_document assembly."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from phase_2_6.clean_document import CLEAN_DOCUMENT_VERSION, build_clean_document_record
from phase_2_6.quality import aggregate, parse_success
from phase_2_6.sections import markdown_heading_sections


class TestSections(unittest.TestCase):
    def test_headings_exclusive_end(self):
        text = "# A\nxx\n## B\nyy\n"
        secs = markdown_heading_sections(text)
        self.assertGreaterEqual(len(secs), 2)
        self.assertEqual(secs[0]["title"], "A")
        self.assertEqual(secs[1]["title"], "B")
        self.assertEqual(secs[0]["end_char"], secs[1]["start_char"])
        self.assertEqual(secs[-1]["end_char"], len(text))

    def test_preamble(self):
        text = "intro\n\n# First\nbody\n"
        secs = markdown_heading_sections(text)
        self.assertEqual(secs[0]["title"], "(preamble)")
        self.assertEqual(secs[1]["title"], "First")


class TestQuality(unittest.TestCase):
    def test_parse_success_ok(self):
        self.assertTrue(
            parse_success(
                {
                    "extract_status": "ok",
                    "normalize_status": "ok",
                    "missing_clean_markdown": False,
                    "clean_md_bytes": 100,
                    "doc_metadata_error": None,
                }
            )
        )

    def test_parse_fail_missing_clean(self):
        self.assertFalse(
            parse_success(
                {
                    "extract_status": "ok",
                    "normalize_status": "ok",
                    "missing_clean_markdown": True,
                    "clean_md_bytes": 0,
                    "doc_metadata_error": None,
                }
            )
        )

    def test_aggregate(self):
        rows = [
            {
                "extract_status": "ok",
                "normalize_status": "ok",
                "missing_clean_markdown": False,
                "clean_md_bytes": 10,
                "raw_html_bytes": 100,
                "doc_metadata_error": None,
            },
            {
                "extract_status": "empty_shell",
                "normalize_status": "empty",
                "missing_clean_markdown": False,
                "clean_md_bytes": 1,
                "raw_html_bytes": 50,
                "doc_metadata_error": None,
            },
        ]
        a = aggregate(rows)
        self.assertEqual(a["parse_success_count"], 1)
        self.assertEqual(a["entry_count"], 2)


class TestCleanDocument(unittest.TestCase):
    def test_version(self):
        self.assertTrue(CLEAN_DOCUMENT_VERSION.startswith("2.6"))

    def test_build_writes_sections(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            md = t / "s.md"
            md.write_text("# T\n\nHello\n", encoding="utf-8")
            meta = t / "m.json"
            meta.write_text(json.dumps({"content_sha256": "abc"}), encoding="utf-8")
            out = t / "c.clean.json"
            rec = build_clean_document_record(
                scheme="sch",
                source_url="https://example.invalid/x",
                clean_md_path=md,
                doc_metadata_path=meta,
                raw_html_path=t / "r.html",
                crawl_path=t / "c.json",
                extract_path=t / "e.json",
                normalize_path=t / "n.json",
                clean_document_out=out,
            )
            self.assertEqual(len(rec["sections"]), 1)
            self.assertEqual(rec["sections"][0]["title"], "T")


if __name__ == "__main__":
    unittest.main()
