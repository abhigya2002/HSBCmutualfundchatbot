"""Register Phase 6.3 chat routes on the FastAPI app."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from fastapi import FastAPI
from starlette.requests import Request

from phase_6_3.handler import ChatHandler
from phase_6_3 import import_paths as _import_paths  # noqa: F401 — path bootstrap


def register_chat_routes(
    app: FastAPI,
    config: Mapping[str, Any],
    *,
    service_factory: Callable[[], Any] | None = None,
) -> None:
    """Wire ``POST /chat`` to Phase 5.6 ``GenerationService``."""
    handler = ChatHandler(config=config, service_factory=service_factory)

    @app.post("/chat")
    async def chat(request: Request) -> Any:
        return await handler.handle(request)
