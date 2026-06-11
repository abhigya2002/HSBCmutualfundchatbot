"""HTTP status policy for Phase 6 API transport vs policy outcomes."""

from __future__ import annotations

# Policy outcomes (refusal, abstention, factual) always use HTTP 200 with AnswerEnvelope body.
POLICY_OUTCOME_HTTP_STATUS = 200

# Transport / validation error codes → HTTP status (architecture Phase 6.4).
ERROR_STATUS_MAP: dict[str, int] = {
    # 400 — client validation
    "invalid_body": 400,
    "invalid_utf8": 400,
    "invalid_json": 400,
    "invalid_json_shape": 400,
    "missing_query": 400,
    "empty_query": 400,
    "invalid_query_type": 400,
    "query_too_long": 400,
    "invalid_session_id_type": 400,
    "session_id_too_long": 400,
    "forbidden_field": 400,
    "invalid_request_state": 400,
    # 413 — payload too large (P6-01)
    "payload_too_large": 413,
    # 415 — wrong content type (P6-03)
    "unsupported_media_type": 415,
    # 429 — optional rate limit
    "rate_limit_exceeded": 429,
    # 502/503 — upstream failures (P6-09)
    "bad_gateway": 502,
    "service_unavailable": 503,
    # 501 — reserved for unimplemented routes (Phase 6.2 stub; removed in 6.3)
    "not_implemented": 501,
}


def status_for_error_code(code: str, *, default: int = 400) -> int:
    return ERROR_STATUS_MAP.get(code, default)


def is_policy_outcome_http_status(status_code: int) -> bool:
    return status_code == POLICY_OUTCOME_HTTP_STATUS
