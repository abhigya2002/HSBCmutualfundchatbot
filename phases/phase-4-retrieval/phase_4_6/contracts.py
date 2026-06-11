"""Data contracts for Phase 4.6 retrieval service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

from phase_4_2.contracts import IntentResult
from phase_4_3.contracts import SchemeResolution
from phase_4_5.contracts import RetrievalResponse


@dataclass(frozen=True)
class RetrievalRequest:
    """Architecture contract: query + optional session id (no PII)."""

    query: str
    session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"query": self.query, "session_id": self.session_id}


@dataclass(frozen=True)
class RefusalResponse:
    """Architecture contract for non-retrieval paths."""

    refusal_type: str
    message_hint: str
    citation_url: str
    intent: str = ""
    policy_code: str = ""
    scheme_resolution_status: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(frozen=True)
class RetrieveOutcome:
    """Union wrapper: RetrievalResponse | RefusalResponse plus audit trail."""

    outcome_type: Literal["retrieval", "refusal"]
    query: str
    intent: IntentResult
    scheme_resolution: SchemeResolution
    retrieval: RetrievalResponse | None = None
    refusal: RefusalResponse | None = None
    performance_limited: bool = False
    hybrid_skipped: bool = False
    index_version: str = ""
    embedding_model_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_type": self.outcome_type,
            "query": self.query,
            "performance_limited": self.performance_limited,
            "hybrid_skipped": self.hybrid_skipped,
            "index_version": self.index_version,
            "embedding_model_id": self.embedding_model_id,
            "intent": self.intent.to_dict(),
            "scheme_resolution": self.scheme_resolution.to_dict(),
            "retrieval": self.retrieval.to_dict() if self.retrieval else None,
            "refusal": self.refusal.to_dict() if self.refusal else None,
        }
