"""Phase 6 handoff document generation."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping

from phase_5_1.config_load import phase5_guardrails_root
from phase_5_6 import PHASE_5_6_VERSION


def build_phase6_handoff(
    *,
    eval_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    return {
        "phase": "5.6",
        "phase_5_6_version": PHASE_5_6_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "api_surface": {
            "answer": "GenerationService.answer(GenerationRequest) -> AnswerEnvelope",
            "generation_request": {
                "fields": ["query", "session_id"],
                "notes": "No PII in session_id; stateless/ephemeral sessions recommended for Phase 6.",
            },
            "answer_envelope": {
                "fields": [
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
                ],
                "outcome_types": ["refusal", "factual", "abstention"],
            },
            "assistant_response": {
                "fields": [
                    "answer_type",
                    "body_text",
                    "citation_url",
                    "citation_markdown",
                    "footer_line",
                    "footer_date",
                    "disclaimer_line",
                    "display_text",
                    "evidence_chunk_id",
                    "refusal_type",
                    "validation_passed",
                    "validation_repaired",
                ],
            },
            "chat_endpoint_suggestion": {
                "method": "POST",
                "path": "/chat",
                "request_body": {"query": "string", "session_id": "string (optional)"},
                "response_body": "AnswerEnvelope JSON",
            },
        },
        "middleware_hooks": {
            "pre_generation": {
                "module": "phase_5_2.engine",
                "class": "PreGenerationComplianceEngine",
                "method": "evaluate",
                "input": "Phase 4 RetrieveOutcome",
                "output": "ComplianceDecision",
            },
            "post_generation": {
                "module": "phase_5_5.validator",
                "class": "PostGenerationValidator",
                "method": "validate_and_repair",
                "input": "RefusalAnswer | FactualAnswer draft",
                "output": "ValidationResult -> AssistantResponse",
            },
        },
        "error_and_refusal_payloads": {
            "refusal": "outcome_type=refusal; assistant.refusal_type set; single allowlisted citation",
            "abstention": "outcome_type=abstention; weak/missing evidence path",
            "validation_failure": "validation_passed=false; Phase 6 should not render raw draft to user",
        },
        "evaluation_summary": dict(eval_summary or {}),
    }


def default_handoff_path() -> Path:
    return phase5_guardrails_root() / "artifacts" / "service" / "phase6_generation_handoff.json"


def write_phase6_handoff(path: Path, payload: Mapping[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
