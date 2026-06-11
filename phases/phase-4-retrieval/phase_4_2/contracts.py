"""Data contracts for Phase 4.2 intent classification."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class IntentLabel(str, Enum):
    FACTUAL = "factual"
    PERFORMANCE_INFO = "performance-info"
    ADVISORY = "advisory"
    COMPARISON = "comparison"
    OUT_OF_SCOPE = "out-of-scope"
    MIXED = "mixed"


class IntentAction(str, Enum):
    RETRIEVE = "retrieve"
    REFUSE = "refuse"
    PERFORMANCE_LIMITED = "performance_limited"
    DISAMBIGUATE = "disambiguate"


@dataclass(frozen=True)
class IntentResult:
    """Architecture contract: intent, action, confidence, reasons."""

    intent: str
    action: str
    confidence: float
    reasons: list[str] = field(default_factory=list)
    policy_code: str = ""
    facet: str = ""
    query_normalized: str = ""

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["skip_retrieval"] = self.action in (
            IntentAction.REFUSE.value,
            IntentAction.DISAMBIGUATE.value,
        )
        return d

    @property
    def skip_retrieval(self) -> bool:
        return self.action in (IntentAction.REFUSE.value, IntentAction.DISAMBIGUATE.value)


def action_for_intent(intent: IntentLabel) -> IntentAction:
    mapping = {
        IntentLabel.FACTUAL: IntentAction.RETRIEVE,
        IntentLabel.PERFORMANCE_INFO: IntentAction.PERFORMANCE_LIMITED,
        IntentLabel.ADVISORY: IntentAction.REFUSE,
        IntentLabel.COMPARISON: IntentAction.REFUSE,
        IntentLabel.OUT_OF_SCOPE: IntentAction.REFUSE,
        IntentLabel.MIXED: IntentAction.REFUSE,
    }
    return mapping[intent]
