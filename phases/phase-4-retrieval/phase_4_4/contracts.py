"""Data contracts for Phase 4.4 hybrid retrieval."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(frozen=True)
class CandidateScores:
    vector: float | None = None
    keyword: float | None = None
    fused: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "vector": self.vector,
            "keyword": self.keyword,
            "fused": self.fused,
        }


@dataclass(frozen=True)
class RetrievalCandidate:
    """Architecture contract: chunk_id, text, source_url, scheme, scores."""

    chunk_id: str
    text: str
    source_url: str
    scheme: str
    scores: CandidateScores
    section_title: str = ""
    effective_date: str = ""
    text_preview: str = ""
    channels: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["scores"] = self.scores.to_dict()
        d["channels"] = list(self.channels)
        return d


@dataclass(frozen=True)
class HybridRetrievalResult:
    query: str
    candidates: list[RetrievalCandidate]
    index_version: str = ""
    embedding_model_id: str = ""
    scheme_filter: str | None = None
    source_url_filter: str | None = None
    keyword_channel_used: bool = True
    vector_fallback_only: bool = False
    filtered_off_allowlist: int = 0
    candidate_pool_size: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "query": self.query,
            "index_version": self.index_version,
            "embedding_model_id": self.embedding_model_id,
            "scheme_filter": self.scheme_filter,
            "source_url_filter": self.source_url_filter,
            "keyword_channel_used": self.keyword_channel_used,
            "vector_fallback_only": self.vector_fallback_only,
            "filtered_off_allowlist": self.filtered_off_allowlist,
            "candidate_pool_size": self.candidate_pool_size,
            "candidates": [c.to_dict() for c in self.candidates],
        }
