"""``AnswerEnvelope`` serialization and shape checks."""

from __future__ import annotations

from typing import Any, Mapping

EXPECTED_ENVELOPE_FIELDS = frozenset(
    {
        "outcome_type",
        "query",
        "session_id",
        "retrieval_outcome_type",
        "compliance_decision",
        "compliance_reasons",
        "validation_passed",
        "validation_repaired",
        "assistant",
        "display_text",
        "audit",
    },
)

EXPECTED_OUTCOME_TYPES = frozenset({"refusal", "factual", "abstention"})


def envelope_to_json(envelope: Any) -> dict[str, Any]:
    """Return Phase 5 ``AnswerEnvelope`` JSON unchanged in shape."""
    if hasattr(envelope, "to_dict"):
        data = envelope.to_dict()
    elif isinstance(envelope, dict):
        data = dict(envelope)
    else:
        raise TypeError("Expected AnswerEnvelope or dict")
    validate_envelope_shape(data)
    return data


def validate_envelope_shape(data: Mapping[str, Any]) -> None:
    missing = EXPECTED_ENVELOPE_FIELDS - set(data.keys())
    if missing:
        raise ValueError(f"AnswerEnvelope missing fields: {sorted(missing)}")
    outcome = str(data.get("outcome_type") or "")
    if outcome not in EXPECTED_OUTCOME_TYPES:
        raise ValueError(f"Invalid outcome_type: {outcome!r}")
    assistant = data.get("assistant")
    if not isinstance(assistant, dict):
        raise ValueError("assistant must be an object")
    if not str(data.get("display_text") or "").strip():
        raise ValueError("display_text must be non-empty")
