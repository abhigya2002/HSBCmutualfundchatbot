"""Normalize Phase 4 RetrievalResponse for factual composition."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class NormalizedRetrieval:
    status: Literal["found", "not_found_in_sources", ""]
    query: str
    chunk_id: str
    chunk_text: str
    citation_url: str
    section_title: str
    effective_date: str
    scheme: str


def normalize_retrieval(retrieval: Any) -> NormalizedRetrieval:
    if hasattr(retrieval, "chunk_text"):
        status = str(getattr(retrieval, "status", "") or "")
        return NormalizedRetrieval(
            status=status,  # type: ignore[arg-type]
            query=str(getattr(retrieval, "query", "") or ""),
            chunk_id=str(getattr(retrieval, "chunk_id", "") or ""),
            chunk_text=str(getattr(retrieval, "chunk_text", "") or ""),
            citation_url=str(getattr(retrieval, "citation_url", "") or ""),
            section_title=str(getattr(retrieval, "section_title", "") or ""),
            effective_date=str(getattr(retrieval, "effective_date", "") or ""),
            scheme=str(getattr(retrieval, "scheme", "") or ""),
        )
    if isinstance(retrieval, dict):
        return NormalizedRetrieval(
            status=str(retrieval.get("status") or ""),  # type: ignore[arg-type]
            query=str(retrieval.get("query") or ""),
            chunk_id=str(retrieval.get("chunk_id") or ""),
            chunk_text=str(retrieval.get("chunk_text") or ""),
            citation_url=str(retrieval.get("citation_url") or ""),
            section_title=str(retrieval.get("section_title") or ""),
            effective_date=str(retrieval.get("effective_date") or ""),
            scheme=str(retrieval.get("scheme") or ""),
        )
    raise TypeError(f"Expected RetrievalResponse or dict, got {type(retrieval)!r}")
