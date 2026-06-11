"""Tests for Phase 3.6 benchmarks and evaluation helpers."""

from __future__ import annotations

import unittest
from pathlib import Path

from phase_3_6.benchmarks import load_benchmark
from phase_3_6.hybrid_search import HybridHit
from phase_3_6.evaluate import _is_hit
from phase_3_6.paths import default_benchmark_path
from phase_3_6.versioning import build_corpus_index_version


class TestPhase36Benchmark(unittest.TestCase):
    def test_load_benchmark_file(self) -> None:
        queries = load_benchmark(default_benchmark_path())
        self.assertGreaterEqual(len(queries), 10)
        self.assertTrue(all(q.expected_source_url.startswith("https://groww.in/") for q in queries))


class TestPhase36Hit(unittest.TestCase):
    def test_url_hit(self) -> None:
        hits = [
            HybridHit("c1", 1.0, "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth", "hsbc-gilt-fund-direct-growth", "vector"),
        ]
        ok, rank = _is_hit(
            hits,
            "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
            None,
        )
        self.assertTrue(ok)
        self.assertEqual(1, rank)

    def test_miss(self) -> None:
        hits = [
            HybridHit("c1", 1.0, "https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth", "hsbc-midcap-fund-direct-growth", "vector"),
        ]
        ok, _ = _is_hit(
            hits,
            "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
            None,
        )
        self.assertFalse(ok)


class TestPhase36Version(unittest.TestCase):
    def test_explicit_version(self) -> None:
        v = build_corpus_index_version({}, {}, explicit="idx_test")
        self.assertEqual("idx_test", v)


if __name__ == "__main__":
    unittest.main()
