"""Load vector + keyword indexes to verify Phase 3 handoff (Phase 4.1)."""

from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path

from phase_4_1.handoff import HandoffIssue, IndexHandoffContext


@dataclass
class LoadedIndexes:
    vector_index: object
    keyword_index: object
    loaded_chunk_count: int


def _ensure_phase3_on_path(chunking_root: Path, indexing_root: Path) -> None:
    for root in (chunking_root.resolve(), indexing_root.resolve()):
        s = str(root)
        if s not in sys.path:
            sys.path.insert(0, s)


def load_indexes(ctx: IndexHandoffContext, chunking_root: Path, indexing_root: Path) -> tuple[LoadedIndexes | None, list[HandoffIssue]]:
    issues: list[HandoffIssue] = []
    if not ctx.vector_index_dir.is_dir() or not ctx.bm25_index_path.is_file():
        issues.append(HandoffIssue("error_prerequisites", "vector dir or bm25 index missing"))
        return None, issues

    _ensure_phase3_on_path(chunking_root, indexing_root)
    try:
        from phase_3_4.vector_store import LocalVectorIndex
        from phase_3_5.bm25 import BM25Index
    except ImportError as exc:
        issues.append(HandoffIssue("error_import_phase3", str(exc)))
        return None, issues

    emb_dir = ctx.embeddings_dir
    if emb_dir is None or not emb_dir.is_dir():
        issues.append(HandoffIssue("error_embeddings_dir", "embeddings_dir missing"))
        return None, issues

    try:
        vector_index = LocalVectorIndex.load(ctx.vector_index_dir, emb_dir)
        keyword_index = BM25Index.load(ctx.bm25_index_path)
    except Exception as exc:
        issues.append(HandoffIssue("error_index_load", str(exc)))
        return None, issues

    if vector_index.dimensions <= 0:
        issues.append(HandoffIssue("error_vector_empty", "vector index has no dimensions"))
    if keyword_index.document_count <= 0:
        issues.append(HandoffIssue("error_bm25_empty", "bm25 index has no documents"))

    records_path = ctx.chunk_records_path
    count = 0
    if records_path.is_file():
        rows = json.loads(records_path.read_text(encoding="utf-8"))
        count = len(rows) if isinstance(rows, list) else 0

    vec_count = len(getattr(vector_index, "_vectors", {}))
    if count and vec_count and count != vec_count:
        issues.append(
            HandoffIssue("error_vector_record_mismatch", f"records={count} vectors={vec_count}"),
        )

    return LoadedIndexes(vector_index=vector_index, keyword_index=keyword_index, loaded_chunk_count=count), issues
