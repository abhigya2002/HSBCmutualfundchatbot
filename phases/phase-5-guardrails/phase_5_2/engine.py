"""Pre-generation compliance rule engine (Phase 5.2)."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from phase_5_1.config_load import load_config
from phase_5_1.handoff import ProhibitedPhrases, build_phase5_handoff_context, load_prohibited_phrases
from phase_5_2.contracts import ComplianceDecision, ComposerRoute
from phase_5_2.outcome_adapter import NormalizedOutcome, normalize_outcome
from phase_5_2.query_sanitize import contains_projection_language, sanitize_query

log = logging.getLogger("phase5_guardrails.phase_5_2.engine")


def _compliance_config(config: Mapping[str, Any]) -> dict[str, Any]:
    return dict(config.get("compliance") or {})


class PreGenerationComplianceEngine:
    """Route Phase 4.6 RetrieveOutcome before factual/refusal composers."""

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
        prohibited: ProhibitedPhrases | None = None,
    ) -> None:
        self.config = dict(config or load_config())
        if prohibited is None:
            loaded, _ = load_prohibited_phrases(self.config)
            prohibited = loaded or ProhibitedPhrases([], [], [], [], [])
        self.prohibited = prohibited
        self._rules = _compliance_config(self.config)

    def evaluate(self, outcome: Any) -> ComplianceDecision:
        normalized = normalize_outcome(outcome)
        return self.evaluate_normalized(normalized, original_query=normalized.query)

    def evaluate_normalized(
        self,
        outcome: NormalizedOutcome,
        *,
        original_query: str | None = None,
    ) -> ComplianceDecision:
        query = original_query if original_query is not None else outcome.query
        sanitize = sanitize_query(query, self.prohibited) if self._rules.get("strip_query_injection", True) else None
        sanitized_query = sanitize.sanitized_query if sanitize else query.strip()
        reasons: list[str] = []
        audit: dict[str, Any] = {}

        if sanitize and sanitize.injection_detected:
            reasons.append("query_injection_stripped")
            audit["stripped_patterns"] = list(sanitize.stripped_patterns)

        if outcome.outcome_type == "refusal":
            reasons.insert(0, "phase4_refusal_short_circuit")
            if outcome.refusal_type:
                reasons.append(f"refusal_type:{outcome.refusal_type}")
            decision = ComplianceDecision(
                decision="refuse",
                reasons=reasons,
                performance_limited=False,
                composer_route="refusal",
                outcome_type=outcome.outcome_type,
                query=query,
                sanitized_query=sanitized_query,
                refusal_type=outcome.refusal_type,
                retrieval_status="",
                audit={**audit, "hybrid_skipped": outcome.hybrid_skipped},
            )
            log.debug("Compliance refuse — %s", decision.reasons)
            return decision

        if outcome.outcome_type != "retrieval":
            reasons.append(f"unknown_outcome_type:{outcome.outcome_type}")
            return ComplianceDecision(
                decision="abstain",
                reasons=reasons,
                performance_limited=outcome.performance_limited,
                composer_route="abstention",
                outcome_type=outcome.outcome_type,
                query=query,
                sanitized_query=sanitized_query,
                retrieval_status=outcome.retrieval_status,
                audit=audit,
            )

        performance_limited = outcome.performance_limited
        if performance_limited:
            reasons.append("performance_limited_grounding_required")
            projection_hits = contains_projection_language(query, self.prohibited)
            if projection_hits:
                reasons.append("performance_projection_query_detected")
                audit["projection_patterns"] = projection_hits

        chunk_text = outcome.chunk_text.strip()
        not_found = outcome.retrieval_status == "not_found_in_sources"
        empty_evidence = not chunk_text

        if self._rules.get("abstain_on_not_found", True) and (not_found or empty_evidence):
            reasons.append("evidence_empty_not_found_in_sources")
            if outcome.not_found_reason:
                reasons.append(f"not_found_reason:{outcome.not_found_reason}")
            decision = ComplianceDecision(
                decision="abstain",
                reasons=reasons,
                performance_limited=performance_limited,
                composer_route="abstention",
                outcome_type=outcome.outcome_type,
                query=query,
                sanitized_query=sanitized_query,
                retrieval_status=outcome.retrieval_status,
                audit=audit,
            )
            log.debug("Compliance abstain — %s", decision.reasons)
            return decision

        if self._rules.get("require_chunk_text_for_compose", True) and empty_evidence:
            reasons.append("evidence_chunk_missing")
            return ComplianceDecision(
                decision="abstain",
                reasons=reasons,
                performance_limited=performance_limited,
                composer_route="abstention",
                outcome_type=outcome.outcome_type,
                query=query,
                sanitized_query=sanitized_query,
                retrieval_status=outcome.retrieval_status,
                audit=audit,
            )

        reasons.append("retrieval_evidence_present")
        if performance_limited:
            reasons.append("performance_limited_compose_allowed")

        decision = ComplianceDecision(
            decision="allow_compose",
            reasons=reasons,
            performance_limited=performance_limited,
            composer_route="factual",
            outcome_type=outcome.outcome_type,
            query=query,
            sanitized_query=sanitized_query,
            retrieval_status=outcome.retrieval_status,
            audit=audit,
        )
        log.debug("Compliance allow_compose — %s", decision.reasons)
        return decision


def evaluate_compliance(outcome: Any, *, config: Mapping[str, Any] | None = None) -> ComplianceDecision:
    return PreGenerationComplianceEngine(config=config).evaluate(outcome)


def ensure_handoff_ready(config: Mapping[str, Any] | None = None) -> None:
    ctx = build_phase5_handoff_context(dict(config or load_config()))
    errors = [i for i in ctx.issues if i.code.startswith("error_") or i.code.startswith("missing_")]
    if errors:
        raise RuntimeError(
            "Phase 5 handoff not ready: " + "; ".join(f"{e.code}: {e.message}" for e in errors),
        )
