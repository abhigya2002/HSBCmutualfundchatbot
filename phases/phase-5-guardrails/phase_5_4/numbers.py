"""Number grounding checks (P5-09)."""

from __future__ import annotations

import re


_NUMBER_PATTERN = re.compile(
    r"(?:₹\s*)?\d[\d,]*(?:\.\d+)?%?|\b\d[\d,]*(?:\.\d+)?\s*(?:%|percent)\b",
    re.IGNORECASE,
)


def extract_numbers(text: str) -> list[str]:
    return [m.group(0).strip() for m in _NUMBER_PATTERN.finditer(text or "")]


def _normalize_number(value: str) -> str:
    return re.sub(r"[\s,₹]", "", value.lower().replace("percent", "%"))


def audit_number_grounding(body_text: str, chunk_text: str) -> list[str]:
    flags: list[str] = []
    chunk_norm = _normalize_number(chunk_text)
    for num in extract_numbers(body_text):
        if _normalize_number(num) not in chunk_norm:
            flags.append(f"uncited_number:{num}")
    return flags


def strip_uncited_numbers(body_text: str, chunk_text: str) -> tuple[str, list[str]]:
    flags = audit_number_grounding(body_text, chunk_text)
    if not flags:
        return body_text, flags
    cleaned = body_text
    for flag in flags:
        num = flag.split(":", 1)[-1]
        cleaned = cleaned.replace(num, "").strip()
    cleaned = re.sub(r"\s{2,}", " ", cleaned)
    cleaned = re.sub(r"\s+([,.!?])", r"\1", cleaned)
    return cleaned.strip(), flags
