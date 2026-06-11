"""Factual response composer (Phase 5.4)."""

from __future__ import annotations

import logging
import re
from typing import Any, Mapping

from phase_5_1.config_load import load_config
from phase_5_1.handoff import ComposerDefaults, load_composer_defaults
from phase_5_2.contracts import ComplianceDecision
from phase_5_3.citation import build_citation_markdown, resolve_citation_url
from phase_5_3.composer import sentence_count
from phase_5_4.contracts import FactualAnswer
from phase_5_4.env_config import groq_composer_enabled
from phase_5_4.extractive import FactualTemplateSet, compose_body_sentences, load_factual_templates
from phase_5_4.footer import resolve_footer_date
from phase_5_4.groq_composer import compose_body_with_groq
from phase_5_4.numbers import audit_number_grounding, strip_uncited_numbers
from phase_5_4.retrieval_adapter import NormalizedRetrieval, normalize_retrieval

log = logging.getLogger("phase5_guardrails.phase_5_4.composer")


def _factual_config(config: Mapping[str, Any]) -> dict[str, Any]:
    return dict(config.get("factual") or {})


class FactualComposer:
    """Turn Phase 4 retrieval evidence into a <=3-sentence factual draft."""

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
        composer: ComposerDefaults | None = None,
        templates: FactualTemplateSet | None = None,
    ) -> None:
        self.config = dict(config or load_config())
        if composer is None:
            loaded, _ = load_composer_defaults(self.config)
            composer = loaded
        if composer is None:
            raise RuntimeError("composer defaults unavailable")
        self.composer = composer
        self.templates = templates or load_factual_templates(self.config)
        self._rules = _factual_config(self.config)

    def compose(
        self,
        retrieval: Any,
        *,
        performance_limited: bool = False,
    ) -> FactualAnswer:
        normalized = normalize_retrieval(retrieval)
        return self.compose_normalized(normalized, performance_limited=performance_limited)

    def compose_normalized(
        self,
        retrieval: NormalizedRetrieval,
        *,
        performance_limited: bool = False,
    ) -> FactualAnswer:
        if retrieval.status != "found" or not retrieval.chunk_text.strip():
            raise ValueError("Factual composer requires retrieval status=found with chunk_text")

        max_body = int(self._rules.get("max_body_sentences") or 2)
        max_body = min(max_body, self.composer.max_sentences)

        body_text = self._compose_body_text(
            retrieval=retrieval,
            max_body=max_body,
            performance_limited=performance_limited,
        )

        if self._rules.get("strip_uncited_numbers", True):
            body_text, _ = strip_uncited_numbers(body_text, retrieval.chunk_text)
        flags = audit_number_grounding(body_text, retrieval.chunk_text)

        if sentence_count(body_text) > self.composer.max_sentences:
            body_text = self._first_sentence(body_text)
            flags = audit_number_grounding(body_text, retrieval.chunk_text)

        citation_url = resolve_citation_url(retrieval.citation_url, self.composer)
        _, citation_markdown = build_citation_markdown(citation_url, self.composer)
        footer_date, footer_line = resolve_footer_date(retrieval.effective_date, self.composer)

        answer = FactualAnswer(
            body_text=body_text,
            citation_url=citation_url,
            citation_markdown=citation_markdown,
            footer_line=footer_line,
            footer_date=footer_date,
            evidence_chunk_id=retrieval.chunk_id,
            scheme=retrieval.scheme,
            section_title=retrieval.section_title,
            performance_limited=performance_limited,
            disclaimer_line=self.composer.disclaimer_line,
            number_grounding_flags=flags,
        )
        log.debug(
            "Composed factual answer chunk=%s scheme=%s sentences=%d",
            answer.evidence_chunk_id,
            answer.scheme,
            sentence_count(answer.body_text),
        )
        return answer

    def _compose_body_text(
        self,
        *,
        retrieval: NormalizedRetrieval,
        max_body: int,
        performance_limited: bool,
    ) -> str:
        if groq_composer_enabled():
            try:
                return compose_body_with_groq(
                    query=retrieval.query,
                    chunk_text=retrieval.chunk_text,
                    max_sentences=min(max_body, self.composer.max_sentences),
                    performance_limited=performance_limited,
                ).strip()
            except Exception as exc:
                log.warning("Groq factual compose failed; falling back to extractive: %s", exc)

        sentences = compose_body_sentences(
            query=retrieval.query,
            chunk_text=retrieval.chunk_text,
            section_title=retrieval.section_title,
            templates=self.templates,
            max_sentences=max_body,
            performance_limited=performance_limited,
            include_section_clarifier=bool(self._rules.get("include_section_clarifier", True)),
        )
        return " ".join(sentences).strip()

    @staticmethod
    def _first_sentence(text: str) -> str:
        parts = re.split(r"(?<=[.!?])\s+", text.strip(), maxsplit=1)
        return parts[0] if parts else text.strip()

    def compose_from_compliance(
        self,
        decision: ComplianceDecision,
        retrieval: Any,
    ) -> FactualAnswer:
        if decision.decision != "allow_compose" or decision.composer_route != "factual":
            raise ValueError(
                f"Factual composer requires decision=allow_compose and route=factual, got {decision.decision}/{decision.composer_route}",
            )
        return self.compose(retrieval, performance_limited=decision.performance_limited)


def compose_factual(
    retrieval: Any,
    *,
    config: Mapping[str, Any] | None = None,
    performance_limited: bool = False,
) -> FactualAnswer:
    return FactualComposer(config=config).compose(retrieval, performance_limited=performance_limited)
