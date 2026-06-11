"""Load refusal templates and resolve allowlisted citations."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from phase_5_1.config_load import resolve_config_relative
from phase_5_1.handoff import ComposerDefaults
from phase_5_1.registry_bridge import canonicalize_url, is_allowlisted_url, validate_registry_or_raise
from phase_5_3 import REFUSAL_TYPES


@dataclass(frozen=True)
class RefusalTemplateSet:
    templates: dict[str, str]
    fallback_body: str


def default_templates_path(config: Mapping[str, Any]) -> Path:
    rel = str(config.get("refusal_templates_path") or "templates/refusal.templates.json")
    return resolve_config_relative(rel)


def load_refusal_templates(config: Mapping[str, Any], path: Path | None = None) -> RefusalTemplateSet:
    p = path or default_templates_path(config)
    data = json.loads(p.read_text(encoding="utf-8"))
    raw = dict(data.get("templates") or {})
    templates = {key: str((raw.get(key) or {}).get("body") or "").strip() for key in REFUSAL_TYPES}
    fallback = str((data.get("fallback") or {}).get("body") or "").strip()
    return RefusalTemplateSet(templates=templates, fallback_body=fallback)


def body_for_refusal_type(template_set: RefusalTemplateSet, refusal_type: str) -> str:
    body = template_set.templates.get(refusal_type, "").strip()
    if body:
        return body
    return template_set.fallback_body


def _registry_label_for_url(url: str) -> str:
    registry = validate_registry_or_raise()
    canon = canonicalize_url(url)
    for entry in registry.get("entries") or []:
        entry_url = canonicalize_url(str(entry.get("url") or ""))
        if entry_url == canon:
            return str(entry.get("scheme_display_name") or entry.get("scheme") or "Source")
    slug = canon.rstrip("/").split("/")[-1]
    return slug.replace("-", " ").title() if slug else "Source"


def resolve_citation_url(candidate_url: str, composer: ComposerDefaults) -> str:
    default = canonicalize_url(composer.default_citation_url)
    raw = (candidate_url or "").strip()
    if not raw:
        return default

    normalized_input = raw
    if not raw.startswith(("http://", "https://", "//")) and raw.startswith("groww.in"):
        normalized_input = f"https://{raw}"

    try:
        canon = canonicalize_url(normalized_input)
    except Exception:
        return default

    if is_allowlisted_url(canon):
        return canon
    return default


def build_citation_markdown(url: str, composer: ComposerDefaults) -> tuple[str, str]:
    label = _registry_label_for_url(url)
    if url == canonicalize_url(composer.default_citation_url):
        label = composer.default_citation_label or label
    markdown = composer.citation_markdown_template.format(label=label, url=url)
    return label, markdown


def count_markdown_links(text: str) -> int:
    return len(re.findall(r"\[[^\]]+\]\([^)]+\)", text))
