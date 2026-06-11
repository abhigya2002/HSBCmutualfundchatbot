"""Tests for Phase 3.3 validation, dedupe, and quality gates."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from phase_3_1.paths import Phase2ArtifactPaths, Phase3ArtifactPaths
from phase_3_3.dedupe import dedupe_chunks
from phase_3_3.enrich import enrich_chunk_metadata
from phase_3_3.load_bundles import ChunkBundle
from phase_3_3.pipeline import process_bundle
from phase_3_3.validate import validate_chunk_allowlist


class TestPhase33Dedupe(unittest.TestCase):
    def test_exact_duplicates_removed(self) -> None:
        chunks = [
            {"chunk_id": "a", "text": "Same text.", "source_url": "https://groww.in/mutual-funds/x"},
            {"chunk_id": "b", "text": "Same   text.", "source_url": "https://groww.in/mutual-funds/x"},
        ]
        out, stats = dedupe_chunks(chunks, source_url=chunks[0]["source_url"])
        self.assertEqual(1, len(out))
        self.assertEqual(1, stats["exact_duplicates_removed"])


class TestPhase33Allowlist(unittest.TestCase):
    def test_rejects_non_allowlisted_url(self) -> None:
        ch = {"chunk_id": "c1", "text": "x", "source_url": "https://example.com/bad", "scheme": "s"}
        errs, canonical = validate_chunk_allowlist(ch, "s")
        self.assertTrue(errs)
        self.assertIsNone(canonical)

    def test_accepts_canonical_groww_url(self) -> None:
        url = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"
        ch = {"chunk_id": "c1", "text": "x", "source_url": url, "scheme": "hsbc-gilt-fund-direct-growth"}
        errs, canonical = validate_chunk_allowlist(ch, "hsbc-gilt-fund-direct-growth")
        self.assertFalse(errs)
        self.assertEqual(url, canonical)


class TestPhase33Enrich(unittest.TestCase):
    def test_effective_date_fallback(self) -> None:
        ch = enrich_chunk_metadata(
            {"chunk_id": "c1", "text": "hi"},
            scheme="s",
            source_url="https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
            doc_type="groww_scheme_page",
            default_compliance_rank=1,
            effective_date_fallback="2026-05-13T00:00:00+00:00",
        )
        self.assertEqual("2026-05-13T00:00:00+00:00", ch["effective_date"])
        self.assertEqual("phase2_fetched_at", ch["effective_date_source"])


class TestPhase33Pipeline(unittest.TestCase):
    def _bundle(self, scheme: str, url: str, chunks: list[dict]) -> ChunkBundle:
        raw = {"scheme": scheme, "source_url": url, "chunks": chunks}
        return ChunkBundle(scheme=scheme, source_url=url, path=Path("x.chunks.json"), raw=raw)

    def test_zero_chunks_excluded(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            phase2 = Phase2ArtifactPaths(root=base, clean=base, metadata=base, quarantine=base)
            url = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"
            bundle = self._bundle("hsbc-gilt-fund-direct-growth", url, [])
            cfg = {
                "doc_type": "groww_scheme_page",
                "default_compliance_rank": 1,
                "chars_per_token_estimate": 4.0,
                "validation": {},
                "embedding": {"max_input_tokens": 8192},
            }
            result = process_bundle(bundle, cfg, phase2, url)
            self.assertFalse(result.indexable)
            self.assertEqual("excluded_empty", result.status)

    def test_valid_bundle_indexable(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            phase2 = Phase2ArtifactPaths(root=base, clean=base, metadata=base, quarantine=base)
            scheme = "hsbc-gilt-fund-direct-growth"
            url = f"https://groww.in/mutual-funds/{scheme}"
            chunks = [
                {
                    "chunk_id": f"{scheme}_c0000",
                    "text": "Expense ratio 0.48%",
                    "source_url": url,
                    "scheme": scheme,
                    "doc_type": "groww_scheme_page",
                    "section_title": "Fund",
                    "compliance_rank": 1,
                },
            ]
            bundle = self._bundle(scheme, url, chunks)
            cfg = {
                "doc_type": "groww_scheme_page",
                "default_compliance_rank": 1,
                "chars_per_token_estimate": 4.0,
                "validation": {"dedupe_identical_text": True},
                "embedding": {"max_input_tokens": 8192, "model_id": "test"},
            }
            result = process_bundle(bundle, cfg, phase2, url)
            self.assertTrue(result.indexable, result.errors)
            self.assertEqual(1, result.chunk_count_out)


if __name__ == "__main__":
    unittest.main()
