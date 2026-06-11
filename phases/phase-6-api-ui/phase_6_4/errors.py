"""Normalized API error JSON — ``{ \"error\": { \"code\", \"message\" } }``."""

from __future__ import annotations

from typing import Any

from phase_6_4.http_policy import status_for_error_code


def error_response(*, code: str, message: str) -> dict[str, Any]:
    return {"error": {"code": code, "message": message}}


def error_http_status(code: str, *, default: int = 400) -> int:
    return status_for_error_code(code, default=default)


def assert_safe_error_payload(payload: dict[str, Any]) -> None:
    """Reject payloads that leak internal exception details."""
    if set(payload.keys()) != {"error"}:
        raise ValueError(f"Error payload must only contain 'error' key, got {sorted(payload.keys())}")
    err = payload.get("error")
    if not isinstance(err, dict):
        raise ValueError("error must be an object")
    if set(err.keys()) != {"code", "message"}:
        raise ValueError(f"error object must only contain code and message, got {sorted(err.keys())}")
    for key in ("code", "message"):
        if not isinstance(err.get(key), str) or not str(err[key]).strip():
            raise ValueError(f"error.{key} must be a non-empty string")
    leaked = ("traceback", "stack", "exception", "Traceback")
    text = str(err.get("message") or "")
    if any(token in text for token in leaked):
        raise ValueError("error.message must not contain stack trace text")
