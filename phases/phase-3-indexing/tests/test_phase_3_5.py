"""Tests for Phase 3.5 BM25 keyword index."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from phase_3_5.bm25 import BM25Index
from phase_3_5.normalize import normalize_for_keyword_index, tokenize
from phase_3_5.query import is_stopword_only_query


class TestNormalize(unittest.TestCase):
    def test_rupee_and_percent(self) -> None:
        t = normalize_for_keyword_index("Min SIP ₹1,000 and expense ratio 0.48%")
        self.assertIn("inr", t)
        self.assertIn("1000", t)
        self.assertIn("percent", t)


class TestBM25(unittest.TestCase):
    def test_ranks_relevant_chunk(self) -> None:
        idx = BM25Index(facet_phrases=["expense ratio", "exit load"])
        idx.add_document(
            "c1",
            "Expense ratio 0.48%. Minimum SIP ₹1,000.",
            {"scheme": "s1", "source_url": "https://groww.in/mutual-funds/s1", "section_title": "Fund"},
        )
        idx.add_document(
            "c2",
            "Benchmark is NIFTY 50 index.",
            {"scheme": "s1", "source_url": "https://groww.in/mutual-funds/s1", "section_title": "Bench"},
        )
        idx.finalize()
        hits = idx.search("expense ratio", top_k=2)
        self.assertGreaterEqual(len(hits), 1)
        self.assertEqual("c1", hits[0].chunk_id)

    def test_save_load_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bm25.json"
            idx = BM25Index()
            idx.add_document(
                "c1",
                "exit load nil",
                {"scheme": "s", "source_url": "https://groww.in/mutual-funds/s", "section_title": ""},
            )
            idx.finalize()
            idx.save(path)
            loaded = BM25Index.load(path)
            hits = loaded.search("exit load")
            self.assertEqual(1, len(hits))


class TestStopwords(unittest.TestCase):
    def test_stopword_only(self) -> None:
        self.assertTrue(is_stopword_only_query("what is the"))
        self.assertFalse(is_stopword_only_query("exit load"))

    def test_empty_bm25_hits(self) -> None:
        idx = BM25Index()
        idx.add_document(
            "c1",
            "expense ratio",
            {"scheme": "s", "source_url": "https://groww.in/mutual-funds/s", "section_title": ""},
        )
        idx.finalize()
        self.assertEqual([], idx.search("the and or"))


if __name__ == "__main__":
    unittest.main()
