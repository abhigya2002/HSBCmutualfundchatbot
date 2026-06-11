"""End-to-end generation service: 4.6 → 5.2 → (5.3 | 5.4 | abstain) → 5.5."""

from __future__ import annotations

import logging
from typing import Any, Callable, Mapping

from phase_5_1.config_load import load_config
from phase_5_2.engine import PreGenerationComplianceEngine
from phase_5_2.phase4_bridge import retrieve_outcome
from phase_5_3.composer import RefusalComposer
from phase_5_4.composer import FactualComposer
from phase_5_5.validator import PostGenerationValidator
from phase_5_6.abstention import compose_abstention
from phase_5_6.contracts import AnswerEnvelope, GenerationRequest, OutcomeType

log = logging.getLogger("phase5_guardrails.phase_5_6.service")

RetrieveFn = Callable[..., Any]


def _field(outcome: Any, name: str, default: Any = None) -> Any:
    if isinstance(outcome, dict):
        return outcome.get(name, default)
    return getattr(outcome, name, default)


class GenerationService:
    """Public API: answer(query) with full guardrails pipeline."""

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
        retrieve_fn: RetrieveFn | None = None,
        compliance_engine: PreGenerationComplianceEngine | None = None,
        refusal_composer: RefusalComposer | None = None,
        factual_composer: FactualComposer | None = None,
        validator: PostGenerationValidator | None = None,
    ) -> None:
        self.config = dict(config or load_config())
        self.retrieve_fn = retrieve_fn or retrieve_outcome
        self.compliance_engine = compliance_engine or PreGenerationComplianceEngine(config=self.config)
        self.refusal_composer = refusal_composer or RefusalComposer(config=self.config)
        self.factual_composer = factual_composer or FactualComposer(config=self.config)
        self.validator = validator or PostGenerationValidator(config=self.config)

    def answer(self, request: GenerationRequest | str) -> AnswerEnvelope:
        req = request if isinstance(request, GenerationRequest) else GenerationRequest(query=str(request))
        query = req.query.strip()
        outcome = self.retrieve_fn(query, session_id=req.session_id)
        compliance = self.compliance_engine.evaluate(outcome)

        outcome_type: OutcomeType
        draft: Any
        audit: dict[str, Any] = {
            "hybrid_skipped": bool(_field(outcome, "hybrid_skipped", False)),
            "performance_limited": compliance.performance_limited,
            "composer_route": compliance.composer_route,
        }

        if compliance.decision == "refuse":
            refusal = _field(outcome, "refusal")
            if refusal is None:
                raise RuntimeError("Compliance refused but Phase 4 refusal payload missing")
            draft = self.refusal_composer.compose_from_compliance(compliance, refusal)
            outcome_type = "refusal"
            audit["refusal_type"] = _field(refusal, "refusal_type", "")
        elif compliance.decision == "abstain":
            citation_url = ""
            retrieval = _field(outcome, "retrieval")
            if retrieval is not None:
                citation_url = str(_field(retrieval, "citation_url", "") or "")
            else:
                refusal = _field(outcome, "refusal")
                if refusal is not None:
                    citation_url = str(_field(refusal, "citation_url", "") or "")
            draft = compose_abstention(query=query, citation_url=citation_url, config=self.config)
            outcome_type = "abstention"
        elif compliance.decision == "allow_compose":
            retrieval = _field(outcome, "retrieval")
            if retrieval is None:
                raise RuntimeError("Compliance allowed compose but retrieval payload missing")
            draft = self.factual_composer.compose_from_compliance(compliance, retrieval)
            outcome_type = "factual"
            audit["evidence_chunk_id"] = _field(retrieval, "chunk_id", "")
        else:
            draft = compose_abstention(query=query, config=self.config)
            outcome_type = "abstention"
            audit["fallback"] = "unknown_compliance_decision"

        validation = self.validator.validate_and_repair(draft)
        assistant = self.validator.to_assistant_response(validation)

        envelope = AnswerEnvelope(
            outcome_type=outcome_type,
            query=query,
            session_id=req.session_id,
            retrieval_outcome_type=str(_field(outcome, "outcome_type", "")),
            compliance_decision=compliance.decision,
            compliance_reasons=list(compliance.reasons),
            validation_passed=validation.passed,
            validation_repaired=validation.repaired,
            assistant=assistant.to_dict(),
            display_text=assistant.display_text,
            audit=audit,
        )
        log.info(
            "answer query=%r outcome=%s validation=%s",
            query[:80],
            outcome_type,
            "passed" if validation.passed else "failed",
        )
        return envelope


def answer(query: str, *, session_id: str = "") -> AnswerEnvelope:
    return GenerationService().answer(GenerationRequest(query=query, session_id=session_id))
