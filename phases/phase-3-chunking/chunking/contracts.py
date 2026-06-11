"""Chunk payloads and tunable parameters (Phase 3)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

CHUNK_STRATEGY_VERSION = "3.0.0"


@dataclass(frozen=True)
class ChunkingParams:
    """Token-budget knobs (tokens estimated via ``chars_per_token_estimate``)."""

    chars_per_token: float = 4.0
    target_tokens_min: int = 300
    target_tokens_max: int = 600
    overlap_tokens_min: int = 50
    overlap_tokens_max: int = 100

    @classmethod
    def from_mapping(cls, m: Mapping[str, Any]) -> "ChunkingParams":
        return cls(
            chars_per_token=float(m.get("chars_per_token_estimate", 4.0)),
            target_tokens_min=int(m.get("target_tokens_min", 300)),
            target_tokens_max=int(m.get("target_tokens_max", 600)),
            overlap_tokens_min=int(m.get("overlap_tokens_min", 50)),
            overlap_tokens_max=int(m.get("overlap_tokens_max", 100)),
        )

    def overlap_tokens(self) -> int:
        """Use upper overlap bound (within architecture 50–100)."""
        return min(self.overlap_tokens_max, max(self.overlap_tokens_min, self.overlap_tokens_min))


@dataclass
class Chunk:
    """One retrieval slice with mandatory provenance metadata."""

    chunk_id: str
    text: str
    start_char: int
    end_char: int
    source_url: str
    scheme: str
    doc_type: str
    section_title: str
    section_level: int
    effective_date: str | None
    compliance_rank: int
    strategy: str
    extra: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "chunk_id": self.chunk_id,
            "text": self.text,
            "start_char": self.start_char,
            "end_char": self.end_char,
            "source_url": self.source_url,
            "scheme": self.scheme,
            "doc_type": self.doc_type,
            "section_title": self.section_title,
            "section_level": self.section_level,
            "effective_date": self.effective_date,
            "compliance_rank": self.compliance_rank,
            "chunk_strategy_version": CHUNK_STRATEGY_VERSION,
            "strategy": self.strategy,
            **self.extra,
        }
