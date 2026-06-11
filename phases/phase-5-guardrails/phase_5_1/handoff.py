"""Load and validate Phase 4 → Phase 5 retrieval handoff."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from phase_5_1.config_load import resolve_config_relative
from phase_5_1.paths import Phase4HandoffPaths
from phase_5_1.registry_bridge import canonicalize_url, is_allowlisted_url, validate_registry_or_raise


@dataclass
class HandoffIssue:
    code: str
    message: str


@dataclass
class ComposerDefaults:
    max_sentences: int
    citation_format: str
    citation_markdown_template: str
    footer_template: str
    footer_date_unavailable: str
    default_citation_url: str
    default_citation_label: str
    disclaimer_line: str


@dataclass
class ProhibitedPhrases:
    advisory_patterns: list[str]
    comparison_patterns: list[str]
    projection_patterns: list[str]
    injection_patterns: list[str]
    regex_patterns: list[str]


@dataclass
class Phase5HandoffContext:
    phase5_handoff: dict[str, Any]
    composer: ComposerDefaults
    prohibited: ProhibitedPhrases
    index_version: str
    embedding_model_id: str
    handoff_path: Path
    registry_entry_count: int
    issues: list[HandoffIssue] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return not any(
            i.code.startswith("error_") or i.code.startswith("missing_")
            for i in self.issues
        )


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def load_prohibited_phrases(config: Mapping[str, Any]) -> tuple[ProhibitedPhrases | None, list[HandoffIssue]]:
    issues: list[HandoffIssue] = []
    rel = str(config.get("prohibited_phrases_path") or "config/prohibited.phrases.json")
    path = resolve_config_relative(rel)
    data = _read_json(path)
    if data is None:
        issues.append(HandoffIssue("missing_prohibited_phrases", str(path)))
        return None, issues
    return (
        ProhibitedPhrases(
            advisory_patterns=list(data.get("advisory_patterns") or []),
            comparison_patterns=list(data.get("comparison_patterns") or []),
            projection_patterns=list(data.get("projection_patterns") or []),
            injection_patterns=list(data.get("injection_patterns") or []),
            regex_patterns=list(data.get("regex_patterns") or []),
        ),
        issues,
    )


def load_composer_defaults(config: Mapping[str, Any]) -> tuple[ComposerDefaults | None, list[HandoffIssue]]:
    issues: list[HandoffIssue] = []
    comp = dict(config.get("composer") or {})
    max_sent = int(comp.get("max_sentences") or 0)
    if max_sent <= 0 or max_sent > 3:
        issues.append(HandoffIssue("composer_max_sentences", f"max_sentences must be 1–3, got {max_sent}"))
    default_url = str(comp.get("default_citation_url") or "")
    if not default_url:
        issues.append(HandoffIssue("missing_default_citation_url", "composer.default_citation_url required"))
    elif not is_allowlisted_url(default_url):
        issues.append(HandoffIssue("default_url_not_allowlisted", default_url))
    return (
        ComposerDefaults(
            max_sentences=max_sent or 3,
            citation_format=str(comp.get("citation_format") or "markdown_link"),
            citation_markdown_template=str(comp.get("citation_markdown_template") or "[{label}]({url})"),
            footer_template=str(comp.get("footer_template") or "Last updated from sources: {date}"),
            footer_date_unavailable=str(comp.get("footer_date_unavailable") or "date unavailable"),
            default_citation_url=canonicalize_url(default_url) if default_url else "",
            default_citation_label=str(comp.get("default_citation_label") or "Source"),
            disclaimer_line=str(comp.get("disclaimer_line") or "Facts-only. No investment advice."),
        ),
        issues,
    )


def validate_phase5_handoff_document(handoff: dict[str, Any]) -> list[HandoffIssue]:
    issues: list[HandoffIssue] = []
    if str(handoff.get("phase")) != "4.6":
        issues.append(HandoffIssue("handoff_phase", f"expected phase 4.6, got {handoff.get('phase')!r}"))

    pins = handoff.get("version_pins") or {}
    if not str(pins.get("index_version") or ""):
        issues.append(HandoffIssue("missing_index_version", "version_pins.index_version"))
    if not str(pins.get("embedding_model_id") or ""):
        issues.append(HandoffIssue("missing_embedding_model_id", "version_pins.embedding_model_id"))

    evidence = handoff.get("evidence_fields_for_phase5") or {}
    for key in ("found", "not_found_in_sources"):
        if not isinstance(evidence.get(key), list) or not evidence.get(key):
            issues.append(HandoffIssue("missing_evidence_fields", f"evidence_fields_for_phase5.{key}"))

    refusal = handoff.get("refusal_contract") or {}
    if not isinstance(refusal.get("fields"), list) or not refusal.get("fields"):
        issues.append(HandoffIssue("missing_refusal_fields", "refusal_contract.fields"))
    types = refusal.get("refusal_types") or []
    if not types:
        issues.append(HandoffIssue("missing_refusal_types", "refusal_contract.refusal_types"))

    perf = handoff.get("performance_limited_flag") or {}
    if not str(perf.get("field") or ""):
        issues.append(HandoffIssue("missing_performance_flag", "performance_limited_flag.field"))

    api = handoff.get("api_surface") or {}
    if "retrieve" not in api:
        issues.append(HandoffIssue("missing_api_surface", "api_surface.retrieve"))

    return issues


def build_phase5_handoff_context(config: Mapping[str, Any]) -> Phase5HandoffContext:
    issues: list[HandoffIssue] = []
    phase4 = Phase4HandoffPaths.from_config(config)
    handoff_path = phase4.default_handoff_path(config)

    handoff = _read_json(handoff_path)
    if handoff is None:
        issues.append(HandoffIssue("missing_phase5_handoff", str(handoff_path)))
        handoff = {}

    composer, comp_issues = load_composer_defaults(config)
    issues.extend(comp_issues)

    prohibited, prob_issues = load_prohibited_phrases(config)
    issues.extend(prob_issues)

    if handoff:
        issues.extend(validate_phase5_handoff_document(handoff))

    registry_count = 0
    try:
        registry = validate_registry_or_raise()
        registry_count = len(registry.get("entries") or [])
        if registry_count != 16:
            issues.append(HandoffIssue("registry_count", f"expected 16 entries, got {registry_count}"))
    except Exception as exc:
        issues.append(HandoffIssue("registry_invalid", str(exc)))

    pins = handoff.get("version_pins") or {}
    return Phase5HandoffContext(
        phase5_handoff=handoff,
        composer=composer or ComposerDefaults(
            max_sentences=3,
            citation_format="markdown_link",
            citation_markdown_template="[{label}]({url})",
            footer_template="Last updated from sources: {date}",
            footer_date_unavailable="date unavailable",
            default_citation_url="",
            default_citation_label="Source",
            disclaimer_line="Facts-only. No investment advice.",
        ),
        prohibited=prohibited
        or ProhibitedPhrases([], [], [], [], []),
        index_version=str(pins.get("index_version") or ""),
        embedding_model_id=str(pins.get("embedding_model_id") or ""),
        handoff_path=handoff_path,
        registry_entry_count=registry_count,
        issues=issues,
    )
