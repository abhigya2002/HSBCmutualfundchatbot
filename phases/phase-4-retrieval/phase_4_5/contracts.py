"""Data contracts for Phase 4.5 re-ranking and citation selection."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal


@dataclass(frozen=True)
class RerankScoreBreakdown:
    vector_norm: float = 0.0
    keyword_norm: float = 0.0
    channel_fused: float = 0.0
    facet_match: float = 0.0
    lexical_overlap: float = 0.0
    scheme_match: float = 0.0
    final_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RankedCandidate:
    chunk_id: str
    chunk_text: str
    source_url: str
    scheme: str
    section_title: str
    effective_date: str
    rank: int
    scores: RerankScoreBreakdown
    channels: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["scores"] = self.scores.to_dict()
        d["channels"] = list(self.channels)
        return d


@dataclass(frozen=True)
class RetrievalResponse:
    """Architecture contract: top candidate + citation_url for Phase 5."""

    status: Literal["found", "not_found_in_sources"]
    query: str
    chunk_id: str
    chunk_text: str
    citation_url: str
    section_title: str
    effective_date: str
    scheme: str
    index_version: str
    embedding_model_id: str
    rank: int
    scores: RerankScoreBreakdown
    ranked_candidates: list[RankedCandidate] = field(default_factory=list)
    citation_precedence: str = ""
    not_found_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "status": self.status,
            "query": self.query,
            "chunk_id": self.chunk_id,
            "chunk_text": self.chunk_text,
            "citation_url": self.citation_url,
            "section_title": self.section_title,
            "effective_date": self.effective_date,
            "scheme": self.scheme,
            "index_version": self.index_version,
            "embedding_model_id": self.embedding_model_id,
            "rank": self.rank,
            "scores": self.scores.to_dict(),
            "citation_precedence": self.citation_precedence,
            "not_found_reason": self.not_found_reason,
            "ranked_candidates": [c.to_dict() for c in self.ranked_candidates],
        }
