"""Enrich chunk metadata (P3-09 effective_date fallback)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from phase_3_1.paths import Phase2ArtifactPaths
from phase_3_2.load import effective_date_from_metadata


def load_phase2_dates(phase2: Phase2ArtifactPaths, scheme: str) -> str | None:
    meta_path = phase2.doc_metadata_path(scheme)
    clean_path = phase2.clean_document_path(scheme)
    doc_meta: dict[str, Any] = {}
    clean_doc: dict[str, Any] = {}
    if meta_path.is_file():
        doc_meta = json.loads(meta_path.read_text(encoding="utf-8"))
    if clean_path.is_file():
        clean_doc = json.loads(clean_path.read_text(encoding="utf-8"))
    return effective_date_from_metadata(doc_meta, clean_doc)


def enrich_chunk_metadata(
    chunk: dict[str, Any],
    *,
    scheme: str,
    source_url: str,
    doc_type: str,
    default_compliance_rank: int,
    effective_date_fallback: str | None,
) -> dict[str, Any]:
    out = dict(chunk)
    out["scheme"] = scheme
    out["source_url"] = source_url
    out["doc_type"] = str(out.get("doc_type") or doc_type)
    out["section_title"] = str(out.get("section_title") or "")
    out["compliance_rank"] = int(out.get("compliance_rank", default_compliance_rank))

    eff = out.get("effective_date")
    if not eff and effective_date_fallback:
        out["effective_date"] = effective_date_fallback
        out["effective_date_source"] = "phase2_fetched_at"
    elif eff:
        out["effective_date"] = str(eff)
        out["effective_date_source"] = out.get("effective_date_source") or "chunk_or_phase2"
    else:
        out["effective_date"] = None
        out["effective_date_source"] = "unknown"

    return out
