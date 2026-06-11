"""HTTP middleware for inbound JSON validation (Phase 6.2)."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from phase_6_4.responses import transport_error_response
from phase_6_2.request_validation import (
    forbidden_field_names,
    limits_from_config,
    validate_chat_request,
)


class InboundValidationMiddleware(BaseHTTPMiddleware):
    """Validate POST bodies on configured paths before route handlers run."""

    def __init__(
        self,
        app: Callable[..., Any],
        *,
        config: Mapping[str, Any],
        validated_paths: frozenset[str] | None = None,
    ) -> None:
        super().__init__(app)
        self._config = dict(config)
        api_cfg = dict(config.get("api") or {})
        paths = validated_paths or frozenset(str(p) for p in (api_cfg.get("validated_post_paths") or ["/chat"]))
        self._validated_paths = paths
        self._limits = limits_from_config(config)
        self._forbidden = forbidden_field_names(config)

    async def dispatch(self, request: Request, call_next: Callable[..., Any]) -> Response:
        if request.method != "POST" or request.url.path not in self._validated_paths:
            return await call_next(request)

        body = await request.body()

        payload, failure, query_length = validate_chat_request(
            content_type=request.headers.get("content-type"),
            body=body,
            limits=self._limits,
            forbidden=self._forbidden,
        )
        if failure:
            return transport_error_response(code=failure.code, message=failure.message, status_code=failure.http_status)

        request.state.validated_payload = payload
        if query_length is not None:
            request.state.validated_query_length = query_length

        async def receive() -> dict[str, Any]:
            return {"type": "http.request", "body": body, "more_body": False}

        replay = Request(request.scope, receive)
        replay.state.validated_payload = payload
        if query_length is not None:
            replay.state.validated_query_length = query_length
        response = await call_next(replay)
        for attr in ("outcome_type", "validation_passed", "validated_query_length"):
            if hasattr(replay.state, attr):
                setattr(request.state, attr, getattr(replay.state, attr))
        return response
