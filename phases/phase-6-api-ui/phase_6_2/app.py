"""FastAPI application factory (Phase 6.2)."""

from __future__ import annotations

from typing import Any, Callable, Mapping

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from phase_6_1.config_load import load_config
from phase_6_1.logging_setup import setup_logging
from phase_6_2.middleware import InboundValidationMiddleware
from phase_6_2.readiness import assess_readiness
from phase_6_2.request_logging import RequestLoggingMiddleware
from phase_6_3.routes import register_chat_routes


def create_app(
    config: Mapping[str, Any] | None = None,
    *,
    service_factory: Callable[[], Any] | None = None,
) -> FastAPI:
    cfg = dict(config or load_config())
    setup_logging(cfg)

    api_cfg = dict(cfg.get("api") or {})
    health_path = str(api_cfg.get("health_path") or "/health")
    readiness_path = str(api_cfg.get("readiness_path") or "/ready")

    app = FastAPI(
        title="HSBC Mutual Fund FAQ Assistant API",
        version="6.4.0",
        description="Phase 6.4 — /chat with standardized HTTP error and outcome contracts.",
    )

    cors = dict(cfg.get("cors") or {})
    origins = [str(x) for x in (cors.get("dev_origins") or [])]
    origins.extend(str(x) for x in (cors.get("prod_origins") or []))
    origins = list(dict.fromkeys(origins))
    if origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=origins,
            allow_credentials=True,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type"],
        )

    log_cfg = dict(cfg.get("logging") or {})
    app.add_middleware(RequestLoggingMiddleware, redact_pii=bool(log_cfg.get("redact_pii", True)))
    app.add_middleware(InboundValidationMiddleware, config=cfg)

    @app.get(health_path)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    @app.get(readiness_path)
    async def ready() -> JSONResponse:
        report = assess_readiness(cfg)
        body = {
            "ready": report.ready,
            "checks": [{"name": c.name, "ok": c.ok, "detail": c.detail} for c in report.checks],
        }
        status = 200 if report.ready else 503
        return JSONResponse(status_code=status, content=body)

    register_chat_routes(app, cfg, service_factory=service_factory)

    return app
