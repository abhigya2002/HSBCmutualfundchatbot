"""Repair path for failed drafts (template citation/footer injection, safe refusal fallback)."""

from __future__ import annotations

from typing import Mapping

from phase_5_1.handoff import ComposerDefaults, ProhibitedPhrases
from phase_5_3.citation import build_citation_markdown, resolve_citation_url
from phase_5_3.composer import RefusalComposer
from phase_5_4.footer import resolve_footer_date
from phase_5_5.contracts import DraftEnvelope, ValidationViolation
from phase_5_5.draft_adapter import envelope_to_dict
from phase_5_5.links import strip_hyperlinks_from_text
from phase_5_5.prohibited import find_prohibited_phrases
from phase_5_5.sentence import truncate_to_sentence_budget
from phase_5_5.validators import collect_violations


def _validation_rules(config: Mapping) -> dict:
    return dict(config.get("validation") or {})


def _violation_codes(violations: list[ValidationViolation]) -> set[str]:
    return {v.code for v in violations}


def repair_draft(
    draft: DraftEnvelope,
    violations: list[ValidationViolation],
    *,
    composer: ComposerDefaults,
    prohibited: ProhibitedPhrases,
    config: Mapping,
) -> tuple[DraftEnvelope, list[str]]:
    """
    Repair precedence:
    1. Strip extra hyperlinks from body.
    2. Normalize/rebuild single allowlisted citation markdown.
    3. Truncate body to sentence budget.
    4. Inject factual footer with approved unavailable date when missing.
    5. If prohibited phrases remain, fall back to safe refusal template.
    """
    rules = _validation_rules(config)
    actions: list[str] = []
    data = draft.to_dict()
    data["number_grounding_flags"] = list(draft.number_grounding_flags)
    working = DraftEnvelope(**data)
    codes = _violation_codes(violations)

    if "body_contains_hyperlink" in codes or "multiple_hyperlinks" in codes:
        working.body_text = strip_hyperlinks_from_text(working.body_text)
        actions.append("strip_body_hyperlinks")

    link_codes = {"citation_link_count", "citation_not_allowlisted", "citation_host_or_scheme"}
    if link_codes & codes or not working.citation_markdown.strip():
        url = resolve_citation_url(working.citation_url, composer)
        _, markdown = build_citation_markdown(url, composer)
        working.citation_url = url
        working.citation_markdown = markdown
        actions.append("rebuild_citation_markdown")

    if "sentence_budget_exceeded" in codes:
        max_sentences = int(rules.get("max_sentences") or composer.max_sentences or 3)
        working.body_text = truncate_to_sentence_budget(
            working.body_text,
            max_sentences,
            count_semicolon_clauses=bool(rules.get("count_semicolon_clauses", True)),
        )
        actions.append("truncate_sentence_budget")

    footer_codes = {"missing_footer", "missing_footer_date", "footer_date_mismatch"}
    if working.answer_type == "factual" and footer_codes & codes:
        footer_date, footer_line = resolve_footer_date("", composer)
        working.footer_date = footer_date
        working.footer_line = footer_line
        actions.append("inject_footer_unavailable")

    remaining = collect_violations(working, composer=composer, prohibited=prohibited, config=config)
    prohibited_hits = find_prohibited_phrases(working.body_text, prohibited)
    needs_fallback = bool(prohibited_hits) or any(v.code == "prohibited_phrase" for v in remaining)

    if needs_fallback and bool(rules.get("fallback_to_refusal_on_failure", True)):
        refusal_type = str(rules.get("fallback_refusal_type") or "advisory")
        refusal = RefusalComposer(config=config, composer=composer).compose(
            {
                "refusal_type": refusal_type,
                "message_hint": "validation_fallback",
                "citation_url": working.citation_url or composer.default_citation_url,
            },
        )
        working = DraftEnvelope(
            answer_type="refusal",
            body_text=refusal.body_text,
            citation_url=refusal.citation_url,
            citation_markdown=refusal.citation_markdown,
            disclaimer_line=refusal.disclaimer_line,
            refusal_type=refusal.refusal_type,
        )
        actions.append(f"fallback_refusal:{refusal_type}")

    return working, actions
