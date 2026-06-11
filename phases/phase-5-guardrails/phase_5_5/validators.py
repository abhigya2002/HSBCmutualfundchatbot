"""Individual post-generation validators."""

from __future__ import annotations

from typing import Mapping

from phase_5_1.handoff import ComposerDefaults, ProhibitedPhrases
from phase_5_3.citation import count_markdown_links
from phase_5_4.numbers import audit_number_grounding
from phase_5_5.contracts import DraftEnvelope, ValidationViolation
from phase_5_5.links import count_hyperlinks, validate_citation_url
from phase_5_5.prohibited import find_prohibited_phrases
from phase_5_5.sentence import count_sentences


def _validation_rules(config: Mapping) -> dict:
    return dict(config.get("validation") or {})


def validate_sentence_budget(
    draft: DraftEnvelope,
    composer: ComposerDefaults,
    config: Mapping,
) -> list[ValidationViolation]:
    rules = _validation_rules(config)
    max_sentences = int(rules.get("max_sentences") or composer.max_sentences or 3)
    count_semicolons = bool(rules.get("count_semicolon_clauses", True))
    total = count_sentences(draft.body_text, count_semicolon_clauses=count_semicolons)
    if total > max_sentences:
        return [
            ValidationViolation(
                code="sentence_budget_exceeded",
                message=f"body has {total} sentences/clauses; max {max_sentences}",
            ),
        ]
    return []


def validate_link_policy(draft: DraftEnvelope) -> list[ValidationViolation]:
    violations: list[ValidationViolation] = []
    body_links = count_hyperlinks(draft.body_text)
    citation_md_links = count_markdown_links(draft.citation_markdown)

    if body_links > 0:
        violations.append(
            ValidationViolation(
                code="body_contains_hyperlink",
                message=f"body must not contain links (found {body_links})",
            ),
        )
    if citation_md_links != 1:
        violations.append(
            ValidationViolation(
                code="citation_link_count",
                message=f"expected exactly one markdown citation link, found {citation_md_links}",
            ),
        )

    ok, _, code = validate_citation_url(draft.citation_url)
    if not ok:
        violations.append(
            ValidationViolation(
                code=code or "citation_not_allowlisted",
                message=f"citation_url not allowlisted: {draft.citation_url!r}",
            ),
        )
    return violations


def validate_prohibited_phrases(
    draft: DraftEnvelope,
    prohibited: ProhibitedPhrases,
) -> list[ValidationViolation]:
    if draft.answer_type == "refusal":
        return []
    hits = find_prohibited_phrases(draft.body_text, prohibited)
    return [
        ValidationViolation(code="prohibited_phrase", message=hit)
        for hit in hits
    ]


def validate_disclaimer(draft: DraftEnvelope, composer: ComposerDefaults, config: Mapping) -> list[ValidationViolation]:
    if not bool(_validation_rules(config).get("require_disclaimer", True)):
        return []
    expected = composer.disclaimer_line.strip()
    if expected and expected not in (draft.disclaimer_line or ""):
        return [
            ValidationViolation(
                code="missing_disclaimer",
                message="disclaimer_line missing or incorrect",
            ),
        ]
    return []


def validate_footer(
    draft: DraftEnvelope,
    composer: ComposerDefaults,
    config: Mapping,
) -> list[ValidationViolation]:
    if draft.answer_type != "factual":
        return []
    if not bool(_validation_rules(config).get("require_footer_for_factual", True)):
        return []

    violations: list[ValidationViolation] = []
    prefix = composer.footer_template.split("{date}")[0].strip()
    footer_line = (draft.footer_line or "").strip()
    footer_date = (draft.footer_date or "").strip()
    unavailable = composer.footer_date_unavailable

    if not footer_line or prefix not in footer_line:
        violations.append(
            ValidationViolation(code="missing_footer", message="footer_line missing required template"),
        )
    if not footer_date:
        violations.append(
            ValidationViolation(code="missing_footer_date", message="footer_date required for factual answers"),
        )
    elif footer_date != unavailable and footer_date not in footer_line:
        violations.append(
            ValidationViolation(
                code="footer_date_mismatch",
                message="footer_date must match footer_line or use unavailable copy",
            ),
        )
    return violations


def validate_number_grounding(draft: DraftEnvelope) -> list[ValidationViolation]:
    if draft.answer_type != "factual":
        return []
    flags = list(draft.number_grounding_flags)
    if draft.chunk_text.strip():
        flags = audit_number_grounding(draft.body_text, draft.chunk_text)
    return [
        ValidationViolation(code=flag, message="uncited numeric in factual body")
        for flag in flags
        if flag.startswith("uncited_number:")
    ]


def collect_violations(
    draft: DraftEnvelope,
    *,
    composer: ComposerDefaults,
    prohibited: ProhibitedPhrases,
    config: Mapping,
) -> list[ValidationViolation]:
    violations: list[ValidationViolation] = []
    violations.extend(validate_sentence_budget(draft, composer, config))
    violations.extend(validate_link_policy(draft))
    violations.extend(validate_prohibited_phrases(draft, prohibited))
    violations.extend(validate_disclaimer(draft, composer, config))
    violations.extend(validate_footer(draft, composer, config))
    violations.extend(validate_number_grounding(draft))
    if not draft.body_text.strip():
        violations.append(ValidationViolation(code="empty_body", message="body_text is empty"))
    return violations
