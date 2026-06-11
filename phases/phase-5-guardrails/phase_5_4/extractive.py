"""Extractive factual answer generation from retrieved chunk text."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from phase_5_1.config_load import resolve_config_relative
from phase_5_4 import FACET_IDS


@dataclass(frozen=True)
class FactualTemplateSet:
    sentence_templates: dict[str, str]
    clarifiers: dict[str, str]


_FACET_PATTERNS: dict[str, list[re.Pattern[str]]] = {
    "expense_ratio": [
        re.compile(r"(?i)expense ratio[^0-9%]*([0-9]+(?:\.[0-9]+)?\s*%)"),
        re.compile(r"(?i)\bTER\b[^0-9%]*([0-9]+(?:\.[0-9]+)?\s*%)"),
    ],
    "exit_load": [
        re.compile(r"(?i)exit load[^.\n]{0,80}?(Nil|[0-9]+(?:\.[0-9]+)?\s*%)"),
    ],
    "min_sip": [
        re.compile(r"(?i)min\.?\s*for\s*sip[^₹0-9]*([₹][0-9,]+|[0-9,]+)"),
    ],
    "min_investment": [
        re.compile(r"(?i)min\.?\s*for\s*1st\s*investment[^₹0-9]*([₹][0-9,]+|[0-9,]+)"),
        re.compile(r"(?i)minimum\s+lumpsum\s+investment[^₹0-9]*([₹][0-9,]+|[0-9,]+)", re.I),
    ],
    "benchmark": [
        re.compile(r"(?i)fund benchmark\s+([A-Z0-9][A-Z0-9 \-]+)"),
        re.compile(r"(?i)benchmark index\s+([A-Z0-9][A-Z0-9 \-]+)"),
    ],
    "riskometer": [
        re.compile(r"(?i)(?:rated|riskometer)\s+([A-Za-z ]{3,30})\s+risk"),
        re.compile(r"(?i)riskometer[^A-Za-z]{0,20}([A-Za-z ]{3,30})"),
    ],
}

_QUERY_FACET_HINTS: list[tuple[str, tuple[str, ...]]] = [
    ("expense_ratio", ("expense ratio", "ter", "total expense")),
    ("exit_load", ("exit load", "redemption charge")),
    ("min_sip", ("minimum sip", "min sip", "sip amount")),
    ("min_investment", ("minimum investment", "min investment", "lumpsum", "first investment")),
    ("benchmark", ("benchmark", "benchmark index")),
    ("riskometer", ("riskometer", "risk rating", "risk level")),
]

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")


def default_templates_path(config: Mapping[str, Any]) -> Path:
    rel = str(config.get("factual_templates_path") or "templates/factual.templates.json")
    return resolve_config_relative(rel)


def load_factual_templates(config: Mapping[str, Any], path: Path | None = None) -> FactualTemplateSet:
    p = path or default_templates_path(config)
    data = json.loads(p.read_text(encoding="utf-8"))
    raw = dict(data.get("sentence_templates") or {})
    templates = {key: str(raw.get(key) or "").strip() for key in FACET_IDS}
    clarifiers = {k: str(v) for k, v in dict(data.get("clarifiers") or {}).items()}
    return FactualTemplateSet(sentence_templates=templates, clarifiers=clarifiers)


def detect_facet(query: str, chunk_text: str) -> str:
    q = query.lower()
    for facet, hints in _QUERY_FACET_HINTS:
        if any(h in q for h in hints):
            return facet
    lowered = chunk_text.lower()
    for facet in ("expense_ratio", "exit_load", "min_sip", "benchmark", "riskometer"):
        if facet.replace("_", " ") in lowered or facet in lowered:
            return facet
    return "generic"


def _extract_value(facet: str, chunk_text: str) -> str:
    for pattern in _FACET_PATTERNS.get(facet, []):
        match = pattern.search(chunk_text)
        if match:
            return match.group(1).strip()
    return ""


def _sentences_from_chunk(chunk_text: str) -> list[str]:
    cleaned = re.sub(r"\|[^|\n]*\|", " ", chunk_text)
    cleaned = re.sub(r"#+\s*", "", cleaned)
    cleaned = re.sub(r"\s+", " ", cleaned).strip()
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(cleaned) if p.strip()]
    return [p for p in parts if len(p) >= 20 and "|" not in p]


def _score_sentence(query: str, sentence: str) -> int:
    q_tokens = set(re.findall(r"[a-z0-9%]+", query.lower()))
    s_tokens = set(re.findall(r"[a-z0-9%]+", sentence.lower()))
    return len(q_tokens & s_tokens)


def _fallback_sentence(query: str, chunk_text: str) -> str:
    ranked = sorted(_sentences_from_chunk(chunk_text), key=lambda s: _score_sentence(query, s), reverse=True)
    if ranked:
        sentence = ranked[0]
        if len(sentence) > 220:
            sentence = sentence[:217].rstrip() + "..."
        return sentence
    snippet = re.sub(r"\s+", " ", chunk_text).strip()
    return snippet[:220].rstrip() + ("..." if len(snippet) > 220 else "")


def _section_title_usable(title: str) -> bool:
    t = title.strip()
    if not t or t in {"(document)", "(preamble)"}:
        return False
    lowered = t.lower()
    if "view details" in lowered or "also manages" in lowered:
        return False
    if len(t) > 80:
        return False
    return True


def compose_body_sentences(
    *,
    query: str,
    chunk_text: str,
    section_title: str,
    templates: FactualTemplateSet,
    max_sentences: int = 2,
    performance_limited: bool = False,
    include_section_clarifier: bool = True,
) -> list[str]:
    facet = detect_facet(query, chunk_text)
    value = _extract_value(facet, chunk_text)
    sentences: list[str] = []

    if facet != "generic" and value:
        template = templates.sentence_templates.get(facet) or templates.sentence_templates["generic"]
        sentences.append(template.format(value=value, sentence=value))
    else:
        sentence = _fallback_sentence(query, chunk_text)
        template = templates.sentence_templates["generic"]
        sentences.append(template.format(value=sentence, sentence=sentence))

    if performance_limited and len(sentences) < max_sentences:
        clarifier = templates.clarifiers.get("performance_limited", "")
        if clarifier:
            sentences.append(clarifier)

    if (
        include_section_clarifier
        and _section_title_usable(section_title)
        and len(sentences) < max_sentences
    ):
        clarifier_tpl = templates.clarifiers.get("section", "")
        if clarifier_tpl:
            sentences.append(clarifier_tpl.format(section_title=section_title))

    return sentences[:max_sentences]
