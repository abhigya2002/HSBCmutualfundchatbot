"""Data contracts for Phase 5.6 generation service."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

OutcomeType = Literal["refusal", "factual", "abstention"]


@dataclass(frozen=True)
class GenerationRequest:
    """Architecture contract: query + optional session id (no PII)."""

    query: str
    session_id: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {"query": self.query, "session_id": self.session_id}


@dataclass
class AnswerEnvelope:
    """Unified API response after retrieve → compose → validate."""

    outcome_type: OutcomeType
    query: str
    session_id: str
    retrieval_outcome_type: str
    compliance_decision: str
    compliance_reasons: list[str]
    validation_passed: bool
    validation_repaired: bool
    assistant: dict[str, Any]
    display_text: str
    audit: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
