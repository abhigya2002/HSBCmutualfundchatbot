"""Load chunk records aligned with Phase 3.4 vector index."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class ChunkForKeyword:
    chunk_id: str
    text: str
    source_url: str
    scheme: str
    doc_type: str
    section_title: str
    effective_date: str | None
    compliance_rank: int


@dataclass(frozen=True)
class VectorIndexRef:
    index_version: str
    embedding_model_id: str
    vector_index_dir: Path
    chunk_count: int


def load_vector_active_pointer(chunking_artifacts: Path) -> dict[str, Any]:
    path = chunking_artifacts / "indexes" / "vector" / "active.json"
    if not path.is_file():
        raise FileNotFoundError(
            f"Missing vector active pointer: {path} (run Phase 3.4 in phase-3-chunking first)",
        )
    return json.loads(path.read_text(encoding="utf-8"))


def resolve_vector_ref(chunking_artifacts: Path) -> VectorIndexRef:
    active = load_vector_active_pointer(chunking_artifacts)
    index_dir = Path(str(active["vector_index_dir"]))
    if not index_dir.is_dir():
        index_dir = chunking_artifacts / "indexes" / "vector" / str(active["index_version"])
    records_path = index_dir / "chunk_records.json"
    if not records_path.is_file():
        raise FileNotFoundError(f"Missing chunk records: {records_path}")
    return VectorIndexRef(
        index_version=str(active["index_version"]),
        embedding_model_id=str(active.get("embedding_model_id") or ""),
        vector_index_dir=index_dir,
        chunk_count=int(active.get("chunk_count") or 0),
    )


def load_chunks_from_vector_index(vector_index_dir: Path) -> list[ChunkForKeyword]:
    records_path = vector_index_dir / "chunk_records.json"
    rows = json.loads(records_path.read_text(encoding="utf-8"))
    chunks: list[ChunkForKeyword] = []
    for row in rows:
        if not isinstance(row, dict):
            continue
        chunks.append(
            ChunkForKeyword(
                chunk_id=str(row["chunk_id"]),
                text=str(row.get("text") or ""),
                source_url=str(row.get("source_url") or ""),
                scheme=str(row.get("scheme") or ""),
                doc_type=str(row.get("doc_type") or ""),
                section_title=str(row.get("section_title") or ""),
                effective_date=str(row["effective_date"]) if row.get("effective_date") else None,
                compliance_rank=int(row.get("compliance_rank", 1)),
            ),
        )
    return chunks
