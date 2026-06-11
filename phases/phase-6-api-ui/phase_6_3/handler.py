"""POST /chat handler — delegates to Phase 5.6 with timeout and safe errors."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from phase_6_3 import import_paths as _import_paths  # noqa: F401, E402

import asyncio
import logging
from typing import Any, Callable, Mapping

from starlette.requests import Request

from phase_6_4.responses import chat_envelope_response, transport_error_response

log = logging.getLogger("phase6_api_ui.phase_6_3.chat")


class ChatHandler:
    """Policy-first chat handler: returns full ``AnswerEnvelope`` only after Phase 5.5."""

    def __init__(
        self,
        *,
        config: Mapping[str, Any],
        service_factory: Callable[[], Any] | None = None,
    ) -> None:
        self._config = dict(config)
        self._service_factory = service_factory
        server = dict(config.get("server") or {})
        self._timeout_seconds = float(server.get("request_timeout_seconds") or 30)

    def _get_service(self) -> Any:
        if self._service_factory is not None:
            return self._service_factory()
        from phase_6_3.service_bridge import create_generation_service

        return create_generation_service()

    async def handle(self, request: Request):
        payload = getattr(request.state, "validated_payload", None)
        if not isinstance(payload, dict):
            return transport_error_response(
                code="invalid_request_state",
                message="Validated payload missing — ensure InboundValidationMiddleware is active.",
                status_code=400,
            )

        query = str(payload.get("query") or "").strip()
        session_id = str(payload.get("session_id") or "")

        try:
            _import_paths.ensure_project_import_paths()
            from phase_5_6.contracts import GenerationRequest

            service = self._get_service()
            envelope = await asyncio.wait_for(
                asyncio.to_thread(
                    service.answer,
                    GenerationRequest(query=query, session_id=session_id),
                ),
                timeout=self._timeout_seconds,
            )
        except asyncio.TimeoutError:
            log.warning("chat timeout query_length=%d", len(query))
            return transport_error_response(
                code="service_unavailable",
                message="The assistant took too long to respond. Please try again.",
                status_code=503,
            )
        except RuntimeError as exc:
            log.warning("chat runtime error: %s", exc)
            return transport_error_response(
                code="service_unavailable",
                message="The assistant is temporarily unavailable. Please try again later.",
                status_code=503,
            )
        except Exception:
            log.exception("chat unexpected error query_length=%d", len(query))
            return transport_error_response(
                code="bad_gateway",
                message="Something went wrong processing your request. Please try again.",
                status_code=502,
            )

        from phase_6_3.envelope import envelope_to_json

        body = envelope_to_json(envelope)
        request.state.outcome_type = body.get("outcome_type")
        request.state.validation_passed = body.get("validation_passed")

        return chat_envelope_response(body)
