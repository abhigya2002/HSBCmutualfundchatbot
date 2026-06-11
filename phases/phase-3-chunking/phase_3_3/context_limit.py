"""Embedding context limit checks (P3-05)."""

from __future__ import annotations

from typing import Any, Mapping

from chunking.tokenizer import estimate_tokens


def apply_embedding_context_limits(
    chunks: list[dict[str, Any]],
    *,
    max_input_tokens: int,
    chars_per_token: float,
) -> tuple[list[dict[str, Any]], dict[str, int]]:
    """
    Flag chunks whose estimated token count exceeds the embedding model limit.

    Does not truncate text in Phase 3.3; Phase 3.4 may cap or split if needed.
    """
    stats = {"chunks_checked": len(chunks), "chunks_exceeding_limit": 0}
    out: list[dict[str, Any]] = []
    for ch in chunks:
        row = dict(ch)
        est = row.get("estimated_tokens")
        if est is None:
            est = estimate_tokens(str(row.get("text") or ""), chars_per_token=chars_per_token)
            row["estimated_tokens"] = est
        if int(est) > max_input_tokens:
            row["embedding_context_exceeded"] = True
            row["embedding_max_tokens"] = max_input_tokens
            stats["chunks_exceeding_limit"] += 1
        else:
            row["embedding_context_exceeded"] = False
            row["embedding_max_tokens"] = max_input_tokens
        out.append(row)
    return out, stats
