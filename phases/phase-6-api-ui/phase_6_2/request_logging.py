"""Structured request logging without raw user PII (P6-10)."""

from __future__ import annotations

import logging
import time
from typing import Any, Callable

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

log = logging.getLogger("phase6_api_ui.request")


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    def __init__(
        self,
        app: Callable[..., Any],
        *,
        redact_pii: bool = True,
    ) -> None:
        super().__init__(app)
        self._redact_pii = redact_pii

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        start = time.perf_counter()
        query_length = getattr(request.state, "validated_query_length", None)
        outcome_type = getattr(request.state, "outcome_type", None)
        validation_passed = getattr(request.state, "validation_passed", None)
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000.0
        log.info(
            "request method=%s path=%s status=%s latency_ms=%.1f query_length=%s outcome_type=%s validation_passed=%s",
            request.method,
            request.url.path,
            response.status_code,
            elapsed_ms,
            query_length if query_length is not None else "-",
            outcome_type if outcome_type is not None else "-",
            validation_passed if validation_passed is not None else "-",
        )
        return response
