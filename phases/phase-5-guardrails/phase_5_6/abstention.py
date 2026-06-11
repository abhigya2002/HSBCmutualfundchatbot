"""Abstention response composer for Phase 5.2 abstain path."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from phase_5_1.config_load import resolve_config_relative
from phase_5_1.handoff import ComposerDefaults, load_composer_defaults
from phase_5_3.citation import build_citation_markdown, resolve_citation_url
from phase_5_3.contracts import RefusalAnswer


def _template_path(config: Mapping[str, Any]) -> Path:
    rel = str(config.get("abstention_templates_path") or "templates/abstention.templates.json")
    return resolve_config_relative(rel)


def compose_abstention(
    *,
    query: str = "",
    citation_url: str = "",
    config: Mapping[str, Any] | None = None,
    composer: ComposerDefaults | None = None,
) -> RefusalAnswer:
    cfg = dict(config or {})
    if composer is None:
        loaded, _ = load_composer_defaults(cfg)
        composer = loaded
    if composer is None:
        raise RuntimeError("composer defaults unavailable")

    path = _template_path(cfg)
    body = "I could not find enough evidence in our official HSBC sources to answer that question."
    if path.is_file():
        data = json.loads(path.read_text(encoding="utf-8"))
        body = str((data.get("template") or {}).get("body") or body).strip()

    url = resolve_citation_url(citation_url, composer)
    _, markdown = build_citation_markdown(url, composer)
    return RefusalAnswer(
        refusal_type="abstention",
        body_text=body,
        citation_url=url,
        citation_markdown=markdown,
        disclaimer_line=composer.disclaimer_line,
    )
