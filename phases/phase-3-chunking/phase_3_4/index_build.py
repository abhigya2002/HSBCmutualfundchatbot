"""Build embeddings and vector index from validated chunks."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from phase_3_1.paths import Phase3ArtifactPaths
from phase_3_4.load_validated import ChunkRecord, load_indexable_chunks
from phase_3_4.paths import (
    embeddings_version_dir,
    vector_active_pointer_path,
    vector_index_version_dir,
)
from phase_3_4.providers.base import EmbeddingProvider, get_provider
from phase_3_4.vector_store import persist_vector_index
from phase_3_4.versioning import build_index_version


@dataclass
class IndexBuildResult:
    index_version: str
    embedding_model_id: str
    provider: str
    dimensions: int
    chunk_count: int
    embeddings_dir: Path
    index_dir: Path


def _batch_embed(provider: EmbeddingProvider, texts: list[str], batch_size: int) -> list[list[float]]:
    vectors: list[list[float]] = []
    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        vectors.extend(provider.embed_texts(batch))
    return vectors


def build_vector_index(
    phase3: Phase3ArtifactPaths,
    config: Mapping[str, Any],
    *,
    index_version: str | None = None,
    provider: EmbeddingProvider | None = None,
) -> IndexBuildResult:
    chunks = load_indexable_chunks(phase3)
    if not chunks:
        raise RuntimeError("No indexable validated chunks found (run Phase 3.3 first)")

    for ch in chunks:
        if ch.metadata.get("embedding_context_exceeded"):
            raise RuntimeError(
                f"Chunk {ch.chunk_id} exceeds embedding context limit; "
                "re-chunk or raise max_input_tokens before indexing",
            )

    emb = config.get("embedding") or {}
    prov = provider or get_provider(config)
    batch_size = max(1, int(emb.get("batch_size", 32)))
    version = build_index_version(
        embedding_model_id=prov.model_id,
        chunk_count=len(chunks),
        config=config,
        explicit=index_version,
    )

    texts = [c.text for c in chunks]
    vectors = _batch_embed(prov, texts, batch_size)
    if len(vectors) != len(chunks):
        raise RuntimeError("Embedding count mismatch")

    chunk_vectors = {ch.chunk_id: vec for ch, vec in zip(chunks, vectors)}

    emb_dir = embeddings_version_dir(phase3, version)
    index_dir = vector_index_version_dir(phase3, version)
    persist_vector_index(
        emb_dir=emb_dir,
        index_dir=index_dir,
        index_version=version,
        embedding_model_id=prov.model_id,
        provider=str(emb.get("provider", "hash_v1")),
        dimensions=prov.dimensions,
        chunk_vectors=chunk_vectors,
        chunks=chunks,
    )

    return IndexBuildResult(
        index_version=version,
        embedding_model_id=prov.model_id,
        provider=str(emb.get("provider", "hash_v1")),
        dimensions=prov.dimensions,
        chunk_count=len(chunks),
        embeddings_dir=emb_dir,
        index_dir=index_dir,
    )


def activate_index(phase3: Phase3ArtifactPaths, result: IndexBuildResult) -> Path:
    """Write ``active.json`` pointer for Phase 4 retrieval (swap-after-full-build)."""
    pointer = vector_active_pointer_path(phase3)
    pointer.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": "3.4",
        "activated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_version": result.index_version,
        "embedding_model_id": result.embedding_model_id,
        "provider": result.provider,
        "dimensions": result.dimensions,
        "chunk_count": result.chunk_count,
        "embeddings_dir": str(result.embeddings_dir),
        "vector_index_dir": str(result.index_dir),
    }
    pointer.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return pointer
