"""Tests for Phase 3.4 embeddings and vector index."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from phase_3_1.paths import Phase3ArtifactPaths
from phase_3_4.index_build import activate_index, build_vector_index
from phase_3_4.providers.hash_v1 import HashEmbeddingV1
from phase_3_4.vector_store import LocalVectorIndex, cosine_similarity


class TestHashEmbedding(unittest.TestCase):
    def test_deterministic(self) -> None:
        p = HashEmbeddingV1(model_id="hash-embedding-v1", dimensions=64)
        a = p.embed_texts(["expense ratio 0.48%"])[0]
        b = p.embed_texts(["expense ratio 0.48%"])[0]
        self.assertEqual(a, b)
        self.assertEqual(64, len(a))

    def test_different_text_different_vector(self) -> None:
        p = HashEmbeddingV1(dimensions=64)
        a = p.embed_texts(["exit load"])[0]
        b = p.embed_texts(["benchmark index"])[0]
        self.assertNotEqual(a, b)


class TestVectorIndexBuild(unittest.TestCase):
    def _write_validated(self, phase3: Phase3ArtifactPaths, scheme: str, url: str) -> None:
        phase3.chunks_validated.mkdir(parents=True, exist_ok=True)
        bundle = {
            "scheme": scheme,
            "source_url": url,
            "indexable": True,
            "chunks": [
                {
                    "chunk_id": f"{scheme}_c0000",
                    "text": "Expense ratio 0.48%. Minimum SIP ₹1,000.",
                    "source_url": url,
                    "scheme": scheme,
                    "doc_type": "groww_scheme_page",
                    "section_title": "Fund",
                    "compliance_rank": 1,
                    "embedding_context_exceeded": False,
                },
                {
                    "chunk_id": f"{scheme}_c0001",
                    "text": "Exit load is nil. Benchmark NIFTY 50.",
                    "source_url": url,
                    "scheme": scheme,
                    "doc_type": "groww_scheme_page",
                    "section_title": "Terms",
                    "compliance_rank": 1,
                    "embedding_context_exceeded": False,
                },
            ],
        }
        path = phase3.chunks_validated / f"{scheme}.chunks.json"
        path.write_text(json.dumps(bundle), encoding="utf-8")

    def test_build_and_search(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            phase3 = Phase3ArtifactPaths(
                root=root,
                chunks=root / "chunks",
                chunks_validated=root / "chunks_validated",
                embeddings=root / "embeddings",
                indexes=root / "indexes",
                logs=root / "logs",
            )
            phase3.ensure_dirs()
            scheme = "hsbc-gilt-fund-direct-growth"
            url = f"https://groww.in/mutual-funds/{scheme}"
            self._write_validated(phase3, scheme, url)
            cfg = {
                "embedding": {
                    "provider": "hash_v1",
                    "model_id": "hash-embedding-v1",
                    "dimensions": 64,
                    "batch_size": 8,
                },
            }
            result = build_vector_index(phase3, cfg, index_version="test_idx_v1")
            self.assertEqual(2, result.chunk_count)
            activate_index(phase3, result)
            active = json.loads((phase3.indexes / "vector" / "active.json").read_text(encoding="utf-8"))
            self.assertEqual("test_idx_v1", active["index_version"])

            index = LocalVectorIndex.load(result.index_dir, result.embeddings_dir)
            provider = HashEmbeddingV1(dimensions=64)
            q = provider.embed_texts(["expense ratio"])[0]
            hits = index.search(q, top_k=2)
            self.assertGreaterEqual(len(hits), 1)
            self.assertIn("expense", hits[0].text_preview.lower())


class TestCosine(unittest.TestCase):
    def test_identical_high_score(self) -> None:
        v = [1.0, 0.0, 0.0]
        self.assertAlmostEqual(1.0, cosine_similarity(v, v))


if __name__ == "__main__":
    unittest.main()
