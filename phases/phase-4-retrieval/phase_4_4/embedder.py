"""Embedding provider factory pinned to Phase 3 handoff."""

from __future__ import annotations

from typing import Any

from phase_4_1.handoff import IndexHandoffContext


def create_embedder(ctx: IndexHandoffContext) -> Any:
    model_id = str(ctx.embedding_model_id or "hash-embedding-v1")
    if model_id == "hash-embedding-v1":
        from phase_3_4.providers.hash_v1 import HashEmbeddingV1

        dims = 384
        return HashEmbeddingV1(model_id=model_id, dimensions=dims)
    raise ValueError(f"unsupported embedding_model_id: {model_id!r}")
