"""Data contracts for Phase 5.2 pre-generation compliance."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Literal

ComplianceDecisionType = Literal["allow_compose", "refuse", "abstain"]
ComposerRoute = Literal["factual", "refusal", "abstention"]


@dataclass(frozen=True)
class ComplianceDecision:
    """Architecture contract: pre-generation routing before composers 5.3/5.4."""

    decision: ComplianceDecisionType
    reasons: list[str]
    performance_limited: bool
    composer_route: ComposerRoute
    outcome_type: str
    query: str
    sanitized_query: str = ""
    refusal_type: str = ""
    retrieval_status: str = ""
    audit: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
