"""Tests for Phase 4.3 scheme resolution."""

from __future__ import annotations

import json
import unittest

from phase_4_1.config_load import phase4_retrieval_root
from phase_4_3.contracts import SchemeStatus
from phase_4_3.registry_index import RegistryIndex
from phase_4_3.resolver import SchemeResolver, resolve_scheme


class TestRegistryIndex(unittest.TestCase):
    def test_sixteen_schemes(self) -> None:
        idx = RegistryIndex.from_registry()
        self.assertEqual(len(idx.records), 16)
        self.assertEqual(len(idx.by_scheme), 16)


class TestSchemeResolver(unittest.TestCase):
    def setUp(self) -> None:
        self.resolver = SchemeResolver()

    def test_resolved_gilt_display_name(self) -> None:
        r = self.resolver.resolve("expense ratio HSBC Gilt Fund Direct Growth")
        self.assertEqual(r.status, SchemeStatus.RESOLVED.value)
        self.assertEqual(r.scheme, "hsbc-gilt-fund-direct-growth")
        self.assertIn("groww.in/mutual-funds/hsbc-gilt-fund", r.citation_url_candidate)

    def test_alias_nickname(self) -> None:
        r = self.resolver.resolve("exit load midcap wala hsbc")
        self.assertEqual(r.scheme, "hsbc-midcap-fund-direct-growth")
        self.assertEqual(r.status, SchemeStatus.RESOLVED.value)

    def test_typo_fuzzy_gilt(self) -> None:
        r = self.resolver.resolve("TER hsbc giltt fund")
        self.assertEqual(r.scheme, "hsbc-gilt-fund-direct-growth")

    def test_multi_scheme_ambiguous(self) -> None:
        r = self.resolver.resolve("Compare HSBC Midcap Fund and HSBC Small Cap Fund")
        self.assertEqual(r.status, SchemeStatus.AMBIGUOUS.value)
        self.assertGreaterEqual(len(r.matched_schemes), 2)
        self.assertFalse(r.scheme)

    def test_unknown_no_scheme(self) -> None:
        r = self.resolver.resolve("expense ratio ICICI Bluechip")
        self.assertEqual(r.status, SchemeStatus.UNKNOWN.value)
        self.assertEqual(r.scheme, "")

    def test_unknown_generic_query(self) -> None:
        r = self.resolver.resolve("what is expense ratio")
        self.assertEqual(r.status, SchemeStatus.UNKNOWN.value)

    def test_url_in_query(self) -> None:
        url = "https://groww.in/mutual-funds/hsbc-consumption-fund-direct-growth"
        r = self.resolver.resolve(f"riskometer {url}")
        self.assertEqual(r.scheme, "hsbc-consumption-fund-direct-growth")

    def test_infrastructure_typo(self) -> None:
        r = self.resolver.resolve("hsbc infrastrucure fund TER")
        self.assertEqual(r.scheme, "hsbc-infrastructure-fund-direct-growth")


class TestSchemeBenchmark(unittest.TestCase):
    def test_benchmark_file_passes(self) -> None:
        from phase_4_3.run_resolve import run_benchmark

        bench = phase4_retrieval_root() / "benchmarks" / "scheme_benchmark.json"
        if not bench.is_file():
            self.skipTest("scheme_benchmark.json missing")
        report = run_benchmark(SchemeResolver(), bench)
        self.assertEqual(report["passed"], report["total"], report["results"])


class TestResolveHelper(unittest.TestCase):
    def test_resolve_scheme_callable(self) -> None:
        r = resolve_scheme("HSBC Focused Fund expense ratio")
        self.assertEqual(r.scheme, "hsbc-focused-fund-direct-growth")


if __name__ == "__main__":
    unittest.main()
