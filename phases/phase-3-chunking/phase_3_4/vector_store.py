"""Local vector index: persist vectors and cosine search for Phase 4."""

from __future__ import annotations

import json
import math
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase_3_4.load_validated import ChunkRecord
from phase_3_4.paths import (
    chunk_records_path,
    embedding_manifest_path,
    vector_index_manifest_path,
    vectors_store_path,
)


def cosine_similarity(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        raise ValueError("vector dimension mismatch")
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(x * x for x in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


@dataclass
class SearchHit:
    chunk_id: str
    score: float
    scheme: str
    source_url: str
    section_title: str
    text_preview: str


class LocalVectorIndex:
    """In-memory index loaded from Phase 3.4 artifacts."""

    def __init__(
        self,
        *,
        index_version: str,
        embedding_model_id: str,
        dimensions: int,
        vectors: dict[str, list[float]],
        records: dict[str, dict[str, Any]],
    ) -> None:
        self.index_version = index_version
        self.embedding_model_id = embedding_model_id
        self.dimensions = dimensions
        self._vectors = vectors
        self._records = records

    @classmethod
    def load(cls, index_dir: Path, emb_dir: Path) -> "LocalVectorIndex":
        idx_manifest = json.loads(vector_index_manifest_path(index_dir).read_text(encoding="utf-8"))
        emb_manifest = json.loads(embedding_manifest_path(emb_dir).read_text(encoding="utf-8"))
        vectors = json.loads(vectors_store_path(emb_dir).read_text(encoding="utf-8"))
        records_list = json.loads(chunk_records_path(index_dir).read_text(encoding="utf-8"))
        records = {str(r["chunk_id"]): r for r in records_list}
        return cls(
            index_version=str(idx_manifest["index_version"]),
            embedding_model_id=str(emb_manifest["embedding_model_id"]),
            dimensions=int(emb_manifest["dimensions"]),
            vectors={k: list(map(float, v)) for k, v in vectors.items()},
            records=records,
        )

    def search(
        self,
        query_vector: list[float],
        *,
        top_k: int = 5,
        scheme: str | None = None,
        source_url: str | None = None,
    ) -> list[SearchHit]:
        hits: list[SearchHit] = []
        for chunk_id, vec in self._vectors.items():
            rec = self._records.get(chunk_id)
            if not rec:
                continue
            if scheme and str(rec.get("scheme")) != scheme:
                continue
            if source_url and str(rec.get("source_url")) != source_url:
                continue
            score = cosine_similarity(query_vector, vec)
            text = str(rec.get("text") or "")
            hits.append(
                SearchHit(
                    chunk_id=chunk_id,
                    score=score,
                    scheme=str(rec.get("scheme") or ""),
                    source_url=str(rec.get("source_url") or ""),
                    section_title=str(rec.get("section_title") or ""),
                    text_preview=text[:240],
                ),
            )
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]


def persist_vector_index(
    *,
    emb_dir: Path,
    index_dir: Path,
    index_version: str,
    embedding_model_id: str,
    provider: str,
    dimensions: int,
    chunk_vectors: dict[str, list[float]],
    chunks: list[ChunkRecord],
) -> dict[str, Any]:
    emb_dir.mkdir(parents=True, exist_ok=True)
    index_dir.mkdir(parents=True, exist_ok=True)

    emb_manifest = {
        "phase": "3.4",
        "index_version": index_version,
        "embedding_model_id": embedding_model_id,
        "provider": provider,
        "dimensions": dimensions,
        "vector_count": len(chunk_vectors),
    }
    embedding_manifest_path(emb_dir).write_text(json.dumps(emb_manifest, indent=2), encoding="utf-8")
    vectors_store_path(emb_dir).write_text(json.dumps(chunk_vectors, indent=2), encoding="utf-8")

    records_out: list[dict[str, Any]] = []
    for ch in chunks:
        records_out.append(
            {
                "chunk_id": ch.chunk_id,
                "text": ch.text,
                "source_url": ch.source_url,
                "scheme": ch.scheme,
                "doc_type": ch.doc_type,
                "section_title": ch.section_title,
                "effective_date": ch.effective_date,
                "compliance_rank": ch.compliance_rank,
                **ch.metadata,
            },
        )
    chunk_records_path(index_dir).write_text(json.dumps(records_out, indent=2), encoding="utf-8")

    idx_manifest = {
        "phase": "3.4",
        "index_version": index_version,
        "embedding_model_id": embedding_model_id,
        "dimensions": dimensions,
        "chunk_count": len(chunks),
        "embeddings_path": str(vectors_store_path(emb_dir)),
        "records_path": str(chunk_records_path(index_dir)),
    }
    vector_index_manifest_path(index_dir).write_text(json.dumps(idx_manifest, indent=2), encoding="utf-8")
    return idx_manifest
