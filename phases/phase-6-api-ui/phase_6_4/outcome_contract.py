"""Refusal, abstention, and factual outcome contracts for UI branching."""

from __future__ import annotations

from typing import Any, Mapping

from phase_6_1.config_load import load_config

REFUSAL_TYPES = frozenset(
    {
        "advisory",
        "comparison",
        "mixed_intent",
        "out_of_scope",
        "disambiguate",
        "performance_info",
    },
)

DEFAULT_ABSTENTION_CITATION_URL = (
    "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth"
)


def default_abstention_citation_url(config: Mapping[str, Any] | None = None) -> str:
    """Fallback allowlisted URL when abstention has weak/missing evidence (Phase 0 default)."""
    _ = config
    return DEFAULT_ABSTENTION_CITATION_URL


def ui_branch(envelope: Mapping[str, Any]) -> dict[str, str]:
    """
    Stable UI branching hints derived from ``AnswerEnvelope``.

    Not added to the HTTP response body — documented for Phase 6.5 clients.
    """
    outcome = str(envelope.get("outcome_type") or "")
    assistant = envelope.get("assistant") if isinstance(envelope.get("assistant"), dict) else {}
    if outcome == "refusal":
        refusal_type = str(assistant.get("refusal_type") or "unknown")
        return {"branch": "refusal", "refusal_type": refusal_type}
    if outcome == "abstention":
        return {"branch": "abstention", "refusal_type": ""}
    return {"branch": "factual", "refusal_type": ""}


def validate_outcome_contract(envelope: Mapping[str, Any]) -> list[str]:
    """Return human-readable contract violations (empty if OK)."""
    issues: list[str] = []
    outcome = str(envelope.get("outcome_type") or "")
    assistant = envelope.get("assistant")
    if not isinstance(assistant, dict):
        return ["assistant must be an object"]

    display_text = str(envelope.get("display_text") or "").strip()
    if not display_text:
        issues.append("display_text must be non-empty")

    if outcome == "refusal":
        refusal_type = str(assistant.get("refusal_type") or "")
        if not refusal_type:
            issues.append("refusal outcome requires assistant.refusal_type")
        elif refusal_type not in REFUSAL_TYPES:
            issues.append(f"unknown refusal_type: {refusal_type!r}")
        if str(assistant.get("answer_type") or "") not in ("refusal", ""):
            issues.append("refusal outcome expects assistant.answer_type=refusal")
        if not str(assistant.get("display_text") or "").strip():
            issues.append("refusal outcome requires assistant.display_text")

    elif outcome == "abstention":
        if str(assistant.get("answer_type") or "") not in ("abstention", ""):
            issues.append("abstention outcome expects assistant.answer_type=abstention")
        citation = str(assistant.get("citation_url") or "")
        if citation and not citation.startswith("https://groww.in/mutual-funds/"):
            issues.append("abstention citation_url must be allowlisted Groww URL when present")

    elif outcome == "factual":
        if not str(assistant.get("body_text") or "").strip():
            issues.append("factual outcome requires assistant.body_text")
        if not str(assistant.get("citation_url") or "").strip():
            issues.append("factual outcome requires assistant.citation_url")

    if envelope.get("validation_passed") is False:
        # Phase 5 handoff: never expose raw draft — display_text must remain safe validator output.
        if display_text != str(assistant.get("display_text") or "").strip():
            issues.append("validation_passed=false but display_text != assistant.display_text")

    return issues
