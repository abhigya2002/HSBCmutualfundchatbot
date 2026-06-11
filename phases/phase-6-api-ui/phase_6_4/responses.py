"""FastAPI/Starlette JSON response helpers."""

from __future__ import annotations

from typing import Any, Mapping

from fastapi.responses import JSONResponse

from phase_6_4.errors import assert_safe_error_payload, error_http_status, error_response
from phase_6_4.handoff_contract import validate_envelope_against_handoff
from phase_6_4.http_policy import POLICY_OUTCOME_HTTP_STATUS
from phase_6_4.outcome_contract import validate_outcome_contract


def transport_error_response(*, code: str, message: str, status_code: int | None = None) -> JSONResponse:
    body = error_response(code=code, message=message)
    assert_safe_error_payload(body)
    status = status_code if status_code is not None else error_http_status(code)
    return JSONResponse(status_code=status, content=body)


def chat_envelope_response(envelope: Mapping[str, Any]) -> JSONResponse:
    """
    Return ``AnswerEnvelope`` with HTTP 200 for factual, refusal, and abstention.

    Policy outcomes are never transport-level HTTP errors.
    """
    handoff_issues = validate_envelope_against_handoff(envelope)
    if handoff_issues:
        codes = ", ".join(i.code for i in handoff_issues)
        return transport_error_response(
            code="bad_gateway",
            message="Response failed contract validation.",
            status_code=502,
        )

    outcome_issues = validate_outcome_contract(envelope)
    if outcome_issues:
        return transport_error_response(
            code="bad_gateway",
            message="Response failed outcome contract validation.",
            status_code=502,
        )

    return JSONResponse(status_code=POLICY_OUTCOME_HTTP_STATUS, content=dict(envelope))
