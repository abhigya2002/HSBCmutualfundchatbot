"""Normalize Phase 4.6 RetrieveOutcome (object or dict) for compliance evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


@dataclass(frozen=True)
class NormalizedOutcome:
    outcome_type: Literal["retrieval", "refusal"]
    query: str
    performance_limited: bool
    hybrid_skipped: bool
    refusal_type: str
    retrieval_status: str
    chunk_text: str
    not_found_reason: str


def normalize_outcome(outcome: Any) -> NormalizedOutcome:
    if hasattr(outcome, "outcome_type") and hasattr(outcome, "query"):
        return _from_object(outcome)
    if isinstance(outcome, dict):
        return _from_dict(outcome)
    raise TypeError(f"Expected RetrieveOutcome or dict, got {type(outcome)!r}")


def _from_object(outcome: Any) -> NormalizedOutcome:
    refusal_type = ""
    if getattr(outcome, "refusal", None) is not None:
        refusal_type = str(getattr(outcome.refusal, "refusal_type", "") or "")

    retrieval_status = ""
    chunk_text = ""
    not_found_reason = ""
    retrieval = getattr(outcome, "retrieval", None)
    if retrieval is not None:
        retrieval_status = str(getattr(retrieval, "status", "") or "")
        chunk_text = str(getattr(retrieval, "chunk_text", "") or "")
        not_found_reason = str(getattr(retrieval, "not_found_reason", "") or "")

    return NormalizedOutcome(
        outcome_type=str(outcome.outcome_type),
        query=str(outcome.query or ""),
        performance_limited=bool(getattr(outcome, "performance_limited", False)),
        hybrid_skipped=bool(getattr(outcome, "hybrid_skipped", False)),
        refusal_type=refusal_type,
        retrieval_status=retrieval_status,
        chunk_text=chunk_text,
        not_found_reason=not_found_reason,
    )


def _from_dict(data: dict[str, Any]) -> NormalizedOutcome:
    refusal = data.get("refusal") or {}
    retrieval = data.get("retrieval") or {}
    return NormalizedOutcome(
        outcome_type=str(data.get("outcome_type") or ""),
        query=str(data.get("query") or ""),
        performance_limited=bool(data.get("performance_limited")),
        hybrid_skipped=bool(data.get("hybrid_skipped")),
        refusal_type=str(refusal.get("refusal_type") or ""),
        retrieval_status=str(retrieval.get("status") or ""),
        chunk_text=str(retrieval.get("chunk_text") or ""),
        not_found_reason=str(retrieval.get("not_found_reason") or ""),
    )
