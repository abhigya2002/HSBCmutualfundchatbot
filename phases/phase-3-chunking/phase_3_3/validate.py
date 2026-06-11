"""Allowlist and required-field validation (P3-04, P3-08)."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from phase_3_1.registry_bridge import is_allowlisted_url, require_allowlisted

REQUIRED_CHUNK_FIELDS = (
    "chunk_id",
    "text",
    "source_url",
    "scheme",
    "doc_type",
    "section_title",
    "compliance_rank",
)


@dataclass
class ValidationError:
    scheme: str
    chunk_id: str | None
    code: str
    message: str


@dataclass
class SchemeValidationResult:
    scheme: str
    source_url: str
    indexable: bool
    status: str
    chunk_count_in: int = 0
    chunk_count_out: int = 0
    errors: list[ValidationError] = field(default_factory=list)
    dedupe_stats: dict[str, int] = field(default_factory=dict)
    context_stats: dict[str, int] = field(default_factory=dict)
    chunks: list[dict[str, Any]] = field(default_factory=list)

    def hard_failures(self) -> list[ValidationError]:
        return [
            e
            for e in self.errors
            if e.code in ("missing_source_url", "url_not_allowlisted", "invalid_source_url")
        ]


def validate_chunk_allowlist(chunk: Mapping[str, Any], scheme: str) -> tuple[list[ValidationError], str | None]:
    """Return errors and canonical ``source_url`` when valid."""
    errors: list[ValidationError] = []
    cid = str(chunk.get("chunk_id") or "")
    url = chunk.get("source_url")
    if not url or not str(url).strip():
        errors.append(
            ValidationError(scheme, cid or None, "missing_source_url", "chunk missing source_url"),
        )
        return errors, None
    try:
        canonical = require_allowlisted(str(url))
    except Exception as exc:
        code = "url_not_allowlisted" if not is_allowlisted_url(str(url)) else "invalid_source_url"
        errors.append(ValidationError(scheme, cid, code, str(exc)))
        return errors, None

    chunk_scheme = str(chunk.get("scheme") or "")
    if chunk_scheme and chunk_scheme != scheme:
        errors.append(
            ValidationError(
                scheme,
                cid,
                "scheme_mismatch",
                f"chunk scheme {chunk_scheme!r} != bundle scheme {scheme!r}",
            ),
        )
    return errors, canonical


def validate_required_fields(chunk: Mapping[str, Any], scheme: str) -> list[ValidationError]:
    errors: list[ValidationError] = []
    cid = str(chunk.get("chunk_id") or "")
    for field_name in REQUIRED_CHUNK_FIELDS:
        if field_name == "compliance_rank":
            if chunk.get(field_name) is None:
                errors.append(ValidationError(scheme, cid, f"missing_{field_name}", f"missing {field_name}"))
            continue
        if field_name == "section_title":
            continue
        val = chunk.get(field_name)
        if val is None or (isinstance(val, str) and not str(val).strip()):
            errors.append(ValidationError(scheme, cid, f"missing_{field_name}", f"missing {field_name}"))
    if not str(chunk.get("text") or "").strip():
        errors.append(ValidationError(scheme, cid, "empty_text", "chunk text is empty"))
    return errors
