"""Refusal response composer (Phase 5.3)."""

from __future__ import annotations

import logging
import re
from typing import Any, Mapping

from phase_5_1.config_load import load_config
from phase_5_1.handoff import ComposerDefaults, load_composer_defaults
from phase_5_2.contracts import ComplianceDecision
from phase_5_3.citation import (
    RefusalTemplateSet,
    body_for_refusal_type,
    build_citation_markdown,
    count_markdown_links,
    load_refusal_templates,
    resolve_citation_url,
)
from phase_5_3.contracts import RefusalAnswer
from phase_5_3.refusal_adapter import NormalizedRefusal, normalize_refusal

log = logging.getLogger("phase5_guardrails.phase_5_3.composer")

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def sentence_count(text: str) -> int:
    stripped = text.strip()
    if not stripped:
        return 0
    return len([part for part in _SENTENCE_SPLIT.split(stripped) if part.strip()])


class RefusalComposer:
    """Map Phase 4 refusal payloads to policy-compliant RefusalAnswer."""

    def __init__(
        self,
        *,
        config: Mapping[str, Any] | None = None,
        composer: ComposerDefaults | None = None,
        templates: RefusalTemplateSet | None = None,
    ) -> None:
        self.config = dict(config or load_config())
        if composer is None:
            loaded, _ = load_composer_defaults(self.config)
            composer = loaded
        if composer is None:
            raise RuntimeError("composer defaults unavailable")
        self.composer = composer
        self.templates = templates or load_refusal_templates(self.config)

    def compose(self, refusal: Any) -> RefusalAnswer:
        normalized = normalize_refusal(refusal)
        return self.compose_normalized(normalized)

    def compose_normalized(self, refusal: NormalizedRefusal) -> RefusalAnswer:
        body = body_for_refusal_type(self.templates, refusal.refusal_type)
        citation_url = resolve_citation_url(refusal.citation_url, self.composer)
        citation_label, citation_markdown = build_citation_markdown(citation_url, self.composer)

        answer = RefusalAnswer(
            refusal_type=refusal.refusal_type or "unknown",
            body_text=body,
            citation_url=citation_url,
            citation_markdown=citation_markdown,
            disclaimer_line=self.composer.disclaimer_line,
            citation_label=citation_label,
        )
        log.debug("Composed refusal %s — citation %s", answer.refusal_type, answer.citation_url)
        return answer

    def compose_from_compliance(
        self,
        decision: ComplianceDecision,
        refusal: Any,
    ) -> RefusalAnswer:
        if decision.decision != "refuse" or decision.composer_route != "refusal":
            raise ValueError(
                f"Refusal composer requires decision=refuse and route=refusal, got {decision.decision}/{decision.composer_route}",
            )
        return self.compose(refusal)


def compose_refusal(refusal: Any, *, config: Mapping[str, Any] | None = None) -> RefusalAnswer:
    return RefusalComposer(config=config).compose(refusal)
