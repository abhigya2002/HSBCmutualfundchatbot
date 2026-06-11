"""Post-generation validator service (Phase 5.5)."""

from __future__ import annotations

import logging
from typing import Any, Mapping

from phase_5_1.config_load import load_config
from phase_5_1.handoff import ComposerDefaults, ProhibitedPhrases, load_composer_defaults, load_prohibited_phrases
from phase_5_5.contracts import AssistantResponse, DraftEnvelope, ValidationResult
from phase_5_5.draft_adapter import envelope_to_dict, normalize_draft
from phase_5_5.repair import repair_draft
from phase_5_5.validators import collect_violations

log = logging.getLogger("phase5_guardrails.phase_5_5.validator")


class PostGenerationValidator:
    """Validate and optionally repair refusal/factual drafts before Phase 6."""

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
        composer: ComposerDefaults | None = None,
        prohibited: ProhibitedPhrases | None = None,
    ) -> None:
        self.config = dict(config or load_config())
        if composer is None:
            loaded, _ = load_composer_defaults(self.config)
            composer = loaded
        if composer is None:
            raise RuntimeError("composer defaults unavailable")
        if prohibited is None:
            loaded, _ = load_prohibited_phrases(self.config)
            prohibited = loaded or ProhibitedPhrases([], [], [], [], [])
        self.composer = composer
        self.prohibited = prohibited
        self._rules = dict(self.config.get("validation") or {})

    def validate(self, draft: Any) -> ValidationResult:
        envelope = normalize_draft(draft)
        violations = collect_violations(
            envelope,
            composer=self.composer,
            prohibited=self.prohibited,
            config=self.config,
        )
        result = ValidationResult(
            passed=len(violations) == 0,
            violations=violations,
            repaired=False,
            answer_type=envelope.answer_type,
            draft=envelope_to_dict(envelope),
            display_text=_display_text(envelope),
            repair_actions=[],
        )
        log.debug("Validation %s — passed=%s violations=%d", envelope.answer_type, result.passed, len(violations))
        return result

    def validate_and_repair(self, draft: Any) -> ValidationResult:
        envelope = normalize_draft(draft)
        violations = collect_violations(
            envelope,
            composer=self.composer,
            prohibited=self.prohibited,
            config=self.config,
        )
        if not violations:
            return ValidationResult(
                passed=True,
                violations=[],
                repaired=False,
                answer_type=envelope.answer_type,
                draft=envelope_to_dict(envelope),
                display_text=_display_text(envelope),
            )

        if not bool(self._rules.get("enable_repair", True)):
            return ValidationResult(
                passed=False,
                violations=violations,
                repaired=False,
                answer_type=envelope.answer_type,
                draft=envelope_to_dict(envelope),
                display_text=_display_text(envelope),
            )

        repaired_envelope, actions = repair_draft(
            envelope,
            violations,
            composer=self.composer,
            prohibited=self.prohibited,
            config=self.config,
        )
        final_violations = collect_violations(
            repaired_envelope,
            composer=self.composer,
            prohibited=self.prohibited,
            config=self.config,
        )
        return ValidationResult(
            passed=len(final_violations) == 0,
            violations=final_violations,
            repaired=bool(actions),
            answer_type=repaired_envelope.answer_type,
            draft=envelope_to_dict(repaired_envelope),
            display_text=_display_text(repaired_envelope),
            repair_actions=actions,
        )

    def to_assistant_response(self, result: ValidationResult) -> AssistantResponse:
        return AssistantResponse.from_validation(result)


def validate_draft(draft: Any, *, config: Mapping[str, Any] | None = None) -> ValidationResult:
    return PostGenerationValidator(config=config).validate(draft)


def validate_and_repair_draft(draft: Any, *, config: Mapping[str, Any] | None = None) -> ValidationResult:
    return PostGenerationValidator(config=config).validate_and_repair(draft)


def _display_text(envelope: DraftEnvelope) -> str:
    parts = [envelope.body_text.strip(), envelope.citation_markdown.strip()]
    if envelope.answer_type == "factual":
        parts.append(envelope.footer_line.strip())
    parts.append(envelope.disclaimer_line.strip())
    return "\n\n".join(p for p in parts if p)
