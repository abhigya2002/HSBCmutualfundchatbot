"""Build BM25 keyword index from Phase 3.4 chunk records."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from phase_3_5.bm25 import BM25Index
from phase_3_5.config_load import resolve_chunking_artifact_root
from phase_3_5.hybrid_contract import build_hybrid_contract
from phase_3_5.load_chunks import (
    load_chunks_from_vector_index,
    load_vector_active_pointer,
    resolve_vector_ref,
)
from phase_3_5.normalize import normalize_for_keyword_index
from phase_3_5.paths import IndexingArtifactPaths


@dataclass
class KeywordIndexBuildResult:
    index_version: str
    keyword_index_dir: Path
    chunk_count: int
    term_count: int


def build_keyword_index(
    config: Mapping[str, Any],
    indexing_paths: IndexingArtifactPaths,
    *,
    index_version: str | None = None,
) -> KeywordIndexBuildResult:
    chunking_artifacts = resolve_chunking_artifact_root(dict(config))
    vector_ref = resolve_vector_ref(chunking_artifacts)
    version = index_version or vector_ref.index_version

    chunks = load_chunks_from_vector_index(vector_ref.vector_index_dir)
    if not chunks:
        raise RuntimeError("No chunks in vector index chunk_records.json")

    kw_cfg = config.get("keyword") or {}
    index = BM25Index(
        k1=float(kw_cfg.get("bm25_k1", 1.5)),
        b=float(kw_cfg.get("bm25_b", 0.75)),
        facet_phrases=list(kw_cfg.get("facet_phrases") or []),
    )

    for ch in chunks:
        keyword_text = normalize_for_keyword_index(ch.text)
        index.add_document(
            ch.chunk_id,
            keyword_text,
            {
                "source_url": ch.source_url,
                "scheme": ch.scheme,
                "doc_type": ch.doc_type,
                "section_title": ch.section_title,
                "effective_date": ch.effective_date,
                "compliance_rank": ch.compliance_rank,
            },
        )

    index.finalize()

    out_dir = indexing_paths.keyword_version_dir(version)
    out_dir.mkdir(parents=True, exist_ok=True)
    index.save(out_dir / "bm25_index.json")

    manifest = {
        "phase": "3.5",
        "index_version": version,
        "algorithm": "bm25",
        "built_at_utc": datetime.now(timezone.utc).isoformat(),
        "aligned_vector_index_version": vector_ref.index_version,
        "embedding_model_id": vector_ref.embedding_model_id,
        "document_count": index.document_count,
        "term_count": len(index._df),
        "shared_merge_keys": ["chunk_id", "source_url", "scheme"],
        "bm25_k1": index.k1,
        "bm25_b": index.b,
    }
    (out_dir / "keyword_index_manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")

    return KeywordIndexBuildResult(
        index_version=version,
        keyword_index_dir=out_dir,
        chunk_count=index.document_count,
        term_count=len(getattr(index, "_df", {})),
    )


def activate_keyword_index(
    indexing_paths: IndexingArtifactPaths,
    result: KeywordIndexBuildResult,
    config: Mapping[str, Any],
) -> Path:
    chunking_artifacts = resolve_chunking_artifact_root(dict(config))
    vector_active = load_vector_active_pointer(chunking_artifacts)
    manifest = json.loads((result.keyword_index_dir / "keyword_index_manifest.json").read_text(encoding="utf-8"))

    pointer = indexing_paths.keyword_active_pointer()
    pointer.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "phase": "3.5",
        "activated_at_utc": datetime.now(timezone.utc).isoformat(),
        "index_version": result.index_version,
        "keyword_index_dir": str(result.keyword_index_dir),
        "bm25_index_path": str(result.keyword_index_dir / "bm25_index.json"),
        "chunk_count": result.chunk_count,
        "aligned_vector_index_version": vector_active.get("index_version"),
    }
    pointer.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    contract = build_hybrid_contract(
        index_version=result.index_version,
        vector_active=vector_active,
        keyword_index_dir=str(result.keyword_index_dir),
        keyword_manifest=manifest,
        chunk_count=result.chunk_count,
    )
    indexing_paths.hybrid_contract_path().write_text(json.dumps(contract, indent=2), encoding="utf-8")
    return pointer
