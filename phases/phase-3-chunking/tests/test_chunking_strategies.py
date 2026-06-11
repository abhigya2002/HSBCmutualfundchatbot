"""Tests for Phase 3 chunking strategies."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from chunking.contracts import ChunkingParams
from chunking.section_sliding import chunk_markdown_section_sliding
from chunking.table_units import atomic_char_spans, iter_table_spans_in_text


class TestTableUnits(unittest.TestCase):
    def test_table_kept_atomic(self):
        text = "intro\n\n| a | b |\n| 1 | 2 |\n\nafter\n"
        spans = atomic_char_spans(text)
        table_span = next(iter_table_spans_in_text(text))
        self.assertTrue(any(a <= table_span[0] and b >= table_span[1] for a, b in spans))

    def test_paragraph_split(self):
        text = "p1\n\np2\n\n"
        spans = atomic_char_spans(text)
        joined = "".join(text[a:b] for a, b in spans)
        self.assertIn("p1", joined)
        self.assertIn("p2", joined)


class TestSectionSliding(unittest.TestCase):
    def test_respects_section_titles(self):
        first = "# A\n" + ("word " * 200)
        second = "\n\n# B\nsmall\n"
        body = first + second
        doc = {
            "sections": [
                {"level": 1, "title": "A", "start_char": 0, "end_char": len(first)},
                {"level": 1, "title": "B", "start_char": len(first), "end_char": len(body)},
            ]
        }
        params = ChunkingParams(chars_per_token=4.0, target_tokens_min=10, target_tokens_max=40, overlap_tokens_min=2, overlap_tokens_max=5)
        chunks = chunk_markdown_section_sliding(
            body,
            clean_document=doc,
            scheme="test-scheme",
            source_url="https://groww.in/mutual-funds/test-scheme",
            doc_type="groww_scheme_page",
            effective_date=None,
            compliance_rank=1,
            params=params,
        )
        self.assertGreaterEqual(len(chunks), 1)
        self.assertEqual(chunks[0].source_url, "https://groww.in/mutual-funds/test-scheme")
        self.assertEqual(chunks[0].scheme, "test-scheme")

    def test_table_not_split_mid_row(self):
        body = "x\n\n| h1 | h2 |\n| v1 | v2 |\n\ny\n"
        doc = {"sections": [{"level": 0, "title": "doc", "start_char": 0, "end_char": len(body)}]}
        params = ChunkingParams(
            chars_per_token=1.0,
            target_tokens_min=5,
            target_tokens_max=12,
            overlap_tokens_min=1,
            overlap_tokens_max=2,
        )
        chunks = chunk_markdown_section_sliding(
            body,
            clean_document=doc,
            scheme="s",
            source_url="https://groww.in/mutual-funds/s",
            doc_type="groww_scheme_page",
            effective_date="2026-01-01",
            compliance_rank=1,
            params=params,
        )
        table_chunks = [c for c in chunks if "| h1 |" in c.text or "| v1 |" in c.text]
        self.assertTrue(table_chunks)
        self.assertIn("| v1 |", table_chunks[0].text)


if __name__ == "__main__":
    unittest.main()
