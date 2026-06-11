"""Inbound request validation (Phase 6.2)."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any, Mapping


@dataclass(frozen=True)
class ValidationLimits:
    max_request_body_bytes: int
    max_query_length: int
    max_session_id_length: int
    required_content_type: str


@dataclass(frozen=True)
class ValidationFailure:
    code: str
    message: str
    http_status: int


def limits_from_config(config: Mapping[str, Any]) -> ValidationLimits:
    val = dict(config.get("validation") or {})
    return ValidationLimits(
        max_request_body_bytes=int(val.get("max_request_body_bytes") or 16384),
        max_query_length=int(val.get("max_query_length") or 2000),
        max_session_id_length=int(val.get("max_session_id_length") or 128),
        required_content_type=str(val.get("required_content_type") or "application/json"),
    )


def forbidden_field_names(config: Mapping[str, Any]) -> frozenset[str]:
    log_cfg = dict(config.get("logging") or {})
    names = {str(x).lower() for x in (log_cfg.get("redact_field_names") or [])}
    names.update({"pan", "aadhaar", "otp", "account_number"})
    return frozenset(names)


def normalize_content_type(value: str | None) -> str:
    if not value:
        return ""
    return value.split(";", 1)[0].strip().lower()


def validate_content_type(content_type: str | None, limits: ValidationLimits) -> ValidationFailure | None:
    normalized = normalize_content_type(content_type)
    required = limits.required_content_type.lower()
    if normalized != required:
        return ValidationFailure(
            code="unsupported_media_type",
            message=f"Content-Type must be {limits.required_content_type}",
            http_status=415,
        )
    return None


def validate_raw_body(body: bytes, limits: ValidationLimits) -> ValidationFailure | None:
    if b"\x00" in body:
        return ValidationFailure(
            code="invalid_body",
            message="Request body must not contain null bytes",
            http_status=400,
        )
    if len(body) > limits.max_request_body_bytes:
        return ValidationFailure(
            code="payload_too_large",
            message=f"Request body exceeds {limits.max_request_body_bytes} bytes",
            http_status=413,
        )
    return None


def decode_json_body(body: bytes) -> tuple[dict[str, Any] | None, ValidationFailure | None]:
    try:
        text = body.decode("utf-8")
    except UnicodeDecodeError:
        return None, ValidationFailure(
            code="invalid_utf8",
            message="Request body must be valid UTF-8",
            http_status=400,
        )
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return None, ValidationFailure(
            code="invalid_json",
            message="Request body must be valid JSON",
            http_status=400,
        )
    if not isinstance(data, dict):
        return None, ValidationFailure(
            code="invalid_json_shape",
            message="Request body must be a JSON object",
            http_status=400,
        )
    return data, None


def validate_chat_payload(
    data: Mapping[str, Any],
    *,
    limits: ValidationLimits,
    forbidden: frozenset[str],
) -> ValidationFailure | None:
    for key in data:
        if str(key).lower() in forbidden:
            return ValidationFailure(
                code="forbidden_field",
                message=f"Field {key!r} is not accepted",
                http_status=400,
            )

    if "query" not in data:
        return ValidationFailure(
            code="missing_query",
            message="Field 'query' is required",
            http_status=400,
        )

    query = data.get("query")
    if not isinstance(query, str):
        return ValidationFailure(
            code="invalid_query_type",
            message="Field 'query' must be a string",
            http_status=400,
        )
    if not query.strip():
        return ValidationFailure(
            code="empty_query",
            message="Field 'query' must not be empty",
            http_status=400,
        )
    if len(query) > limits.max_query_length:
        return ValidationFailure(
            code="query_too_long",
            message=f"Field 'query' exceeds {limits.max_query_length} characters",
            http_status=400,
        )

    if "session_id" in data:
        session_id = data.get("session_id")
        if session_id is not None and not isinstance(session_id, str):
            return ValidationFailure(
                code="invalid_session_id_type",
                message="Field 'session_id' must be a string when provided",
                http_status=400,
            )
        if isinstance(session_id, str) and len(session_id) > limits.max_session_id_length:
            return ValidationFailure(
                code="session_id_too_long",
                message=f"Field 'session_id' exceeds {limits.max_session_id_length} characters",
                http_status=400,
            )

    return None


def validate_chat_request(
    *,
    content_type: str | None,
    body: bytes,
    limits: ValidationLimits,
    forbidden: frozenset[str],
) -> tuple[dict[str, Any] | None, ValidationFailure | None, int | None]:
    """Return (payload, failure, query_length_for_logging)."""
    failure = validate_content_type(content_type, limits)
    if failure:
        return None, failure, None

    failure = validate_raw_body(body, limits)
    if failure:
        return None, failure, None

    data, failure = decode_json_body(body)
    if failure:
        return None, failure, None
    assert data is not None

    failure = validate_chat_payload(data, limits=limits, forbidden=forbidden)
    if failure:
        query_len = len(str(data.get("query") or "")) if isinstance(data.get("query"), str) else None
        return None, failure, query_len

    return data, None, len(str(data["query"]))
