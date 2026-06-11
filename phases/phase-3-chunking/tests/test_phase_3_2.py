"""Tests for Phase 3.2 chunk persistence and golden table boundaries."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from chunking.contracts import ChunkingParams
from chunking.section_sliding import chunk_markdown_section_sliding
from phase_3_1.paths import Phase2ArtifactPaths, Phase3ArtifactPaths
from phase_3_2.chunk_scheme import chunk_scheme
from phase_3_2.load import load_scheme_chunk_input
from phase_3_2.persist import build_chunk_bundle, write_chunk_bundle
from phase_3_2.paths import chunk_bundle_path


class TestPhase32ShortDocument(unittest.TestCase):
    def test_minimum_one_chunk_when_shorter_than_overlap(self) -> None:
        body = "Expense ratio 0.48%. Min SIP ₹1,000."
        doc = {"sections": [{"level": 0, "title": "doc", "start_char": 0, "end_char": len(body)}]}
        params = ChunkingParams(
            chars_per_token=4.0,
            target_tokens_min=300,
            target_tokens_max=600,
            overlap_tokens_min=50,
            overlap_tokens_max=100,
        )
        chunks = chunk_markdown_section_sliding(
            body,
            clean_document=doc,
            scheme="short-scheme",
            source_url="https://groww.in/mutual-funds/short-scheme",
            doc_type="groww_scheme_page",
            effective_date=None,
            compliance_rank=1,
            params=params,
        )
        self.assertEqual(1, len(chunks))
        self.assertIn("Expense ratio", chunks[0].text)


class TestPhase32Persist(unittest.TestCase):
    def test_write_bundle_roundtrip(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            phase3 = Phase3ArtifactPaths(
                root=root,
                chunks=root / "chunks",
                chunks_validated=root / "chunks_validated",
                embeddings=root / "emb",
                indexes=root / "idx",
                logs=root / "logs",
            )
            phase3.ensure_dirs()
            clean = root / "p2" / "clean"
            meta = root / "p2" / "metadata"
            clean.mkdir(parents=True)
            meta.mkdir(parents=True)
            scheme = "test-scheme"
            body = "# A\n\nHello world.\n"
            md = clean / f"{scheme}.md"
            md.write_text(body, encoding="utf-8")
            url = f"https://groww.in/mutual-funds/{scheme}"
            clean_doc = {
                "scheme": scheme,
                "source_url": url,
                "body_markdown_path": str(md),
                "sections": [{"level": 1, "title": "A", "start_char": 0, "end_char": len(body)}],
                "status_upstream": {"extract_status": "ok", "fetched_at": "2026-01-01T00:00:00+00:00"},
            }
            (clean / f"{scheme}.clean.json").write_text(json.dumps(clean_doc), encoding="utf-8")
            doc_meta = {
                "scheme": scheme,
                "source_url": url,
                "extract_status": "ok",
                "fetched_at": "2026-01-01T00:00:00+00:00",
            }
            (meta / f"{scheme}.json").write_text(json.dumps(doc_meta), encoding="utf-8")

            phase2 = Phase2ArtifactPaths(root=root / "p2", clean=clean, metadata=meta, quarantine=root / "q")
            inp = load_scheme_chunk_input(scheme, url, phase2)
            cfg = {
                "default_strategy": "section_sliding_v1",
                "doc_type": "groww_scheme_page",
                "default_compliance_rank": 1,
            }
            params = ChunkingParams(target_tokens_min=10, target_tokens_max=40, overlap_tokens_min=2, overlap_tokens_max=5)
            chunks = chunk_scheme(inp, cfg, params)
            bundle = build_chunk_bundle(inp, chunks, strategy="section_sliding_v1", chunking_config_snapshot={})
            out = chunk_bundle_path(phase3, scheme)
            write_chunk_bundle(out, bundle)
            loaded = json.loads(out.read_text(encoding="utf-8"))
            self.assertEqual(scheme, loaded["scheme"])
            self.assertGreaterEqual(loaded["chunk_count"], 1)
            self.assertIn("chunk_id", loaded["chunks"][0])


class TestPhase32GoldenTable(unittest.TestCase):
    """Golden boundary: table rows stay intact on a real table-heavy Groww page."""

    _GILT_SLUG = "hsbc-gilt-fund-direct-growth"

    @classmethod
    def setUpClass(cls) -> None:
        cls._phase3_root = Path(__file__).resolve().parents[1]
        cls._phase2 = Phase2ArtifactPaths.from_config(
            {"phase2_artifact_root": str(cls._phase3_root / "../phase-2-ingestion/artifacts")},
        )
        cls._available = cls._phase2.clean_document_path(cls._GILT_SLUG).is_file()

    def test_gilt_table_not_split_mid_row(self) -> None:
        if not self._available:
            self.skipTest("Phase 2 artifacts not present")
        scheme = self._GILT_SLUG
        url = f"https://groww.in/mutual-funds/{scheme}"
        inp = load_scheme_chunk_input(scheme, url, self._phase2)
        params = ChunkingParams.from_mapping(
            {
                "chars_per_token_estimate": 4.0,
                "target_tokens_min": 300,
                "target_tokens_max": 600,
                "overlap_tokens_min": 50,
                "overlap_tokens_max": 100,
            },
        )
        chunks = chunk_scheme(
            inp,
            {"default_strategy": "section_sliding_v1", "doc_type": "groww_scheme_page", "default_compliance_rank": 1},
            params,
        )
        self.assertGreater(len(chunks), 0)
        table_markers = ("| 1 year |", "| 3 years |", "| Over the past |")
        for marker in table_markers:
            if marker not in inp.body:
                continue
            containing = [c for c in chunks if marker in c.text]
            self.assertTrue(containing, f"no chunk contains table marker {marker!r}")
        for c in chunks:
            if "|" not in c.text:
                continue
            lines = [ln for ln in c.text.splitlines() if "|" in ln]
            for ln in lines:
                if ln.strip().startswith("|") and ln.count("|") >= 2:
                    self.assertNotRegex(ln, r"^\|\s*[^|]+\s*$", msg=f"truncated table row in chunk {c.chunk_id}")


if __name__ == "__main__":
    unittest.main()
