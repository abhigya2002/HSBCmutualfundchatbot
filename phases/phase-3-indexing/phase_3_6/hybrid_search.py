"""Minimal hybrid retrieval for benchmark evaluation (Phase 4 preview)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass
class HybridHit:
    chunk_id: str
    score: float
    source_url: str
    scheme: str
    channel: str


def _chunking_root(indexing_root: Path) -> Path:
    return (indexing_root / "../phase-3-chunking").resolve()


def _ensure_chunking_path(indexing_root: Path) -> None:
    root = str(_chunking_root(indexing_root))
    if root not in sys.path:
        sys.path.insert(0, root)


def load_hybrid_indexes(indexing_root: Path) -> tuple[Any, Any, dict[str, Any], dict[str, Any]]:
    _ensure_chunking_path(indexing_root)
    chunking_artifacts = _chunking_root(indexing_root) / "artifacts"

    from phase_3_4.providers.hash_v1 import HashEmbeddingV1
    from phase_3_4.vector_store import LocalVectorIndex
    from phase_3_5.bm25 import BM25Index
    from phase_3_5.load_chunks import load_vector_active_pointer

    vector_active = load_vector_active_pointer(chunking_artifacts)
    vector_dir = Path(str(vector_active["vector_index_dir"]))
    emb_dir = Path(str(vector_active["embeddings_dir"]))

    vector_index = LocalVectorIndex.load(vector_dir, emb_dir)

    kw_active_path = indexing_root / "artifacts" / "indexes" / "keyword" / "active.json"
    kw_active = json.loads(kw_active_path.read_text(encoding="utf-8"))
    kw_dir = Path(str(kw_active["keyword_index_dir"]))
    keyword_index = BM25Index.load(kw_dir / "bm25_index.json")

    return vector_index, keyword_index, vector_active, kw_active


def hybrid_search(
    query: str,
    *,
    vector_index: Any,
    keyword_index: Any,
    embedding_provider: Any,
    top_k: int = 5,
    scheme: str | None = None,
) -> list[HybridHit]:
    from phase_3_5.query import is_stopword_only_query

    merged: dict[str, HybridHit] = {}

    if not is_stopword_only_query(query):
        for hit in keyword_index.search(query, top_k=top_k, scheme=scheme):
            merged[hit.chunk_id] = HybridHit(
                chunk_id=hit.chunk_id,
                score=float(hit.score),
                source_url=hit.source_url,
                scheme=hit.scheme,
                channel="keyword",
            )

    qvec = embedding_provider.embed_texts([query])[0]
    for hit in vector_index.search(qvec, top_k=top_k, scheme=scheme):
        if hit.chunk_id in merged:
            merged[hit.chunk_id].score = max(merged[hit.chunk_id].score, float(hit.score))
            merged[hit.chunk_id].channel = "hybrid"
        else:
            merged[hit.chunk_id] = HybridHit(
                chunk_id=hit.chunk_id,
                score=float(hit.score),
                source_url=hit.source_url,
                scheme=hit.scheme,
                channel="vector",
            )

    ranked = sorted(merged.values(), key=lambda h: h.score, reverse=True)
    return ranked[:top_k]
