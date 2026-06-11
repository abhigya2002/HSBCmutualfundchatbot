"""Load and validate Phase 5.6 → Phase 6 generation handoff."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from phase_6_1.config_load import resolve_config_relative
from phase_6_1.paths import Phase5HandoffPaths


@dataclass
class HandoffIssue:
    code: str
    message: str


@dataclass
class ServerConfig:
    host: str
    port: int
    request_timeout_seconds: int


@dataclass
class ValidationLimits:
    max_request_body_bytes: int
    max_query_length: int
    max_session_id_length: int
    required_content_type: str


@dataclass
class CorsConfig:
    dev_origins: list[str]
    prod_origins: list[str]


@dataclass
class LoggingConfig:
    level: str
    redact_pii: bool
    redact_field_names: list[str]


@dataclass
class Phase6HandoffContext:
    phase6_handoff: dict[str, Any]
    handoff_path: Path
    server: ServerConfig
    validation: ValidationLimits
    cors: CorsConfig
    logging: LoggingConfig
    chat_endpoint_path: str
    answer_envelope_fields: list[str]
    outcome_types: list[str]
    issues: list[HandoffIssue] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return not any(
            i.code.startswith("error_") or i.code.startswith("missing_")
            for i in self.issues
        )


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def load_server_config(config: Mapping[str, Any]) -> tuple[ServerConfig, list[HandoffIssue]]:
    issues: list[HandoffIssue] = []
    srv = dict(config.get("server") or {})
    host = str(srv.get("host") or "").strip()
    port = int(srv.get("port") or 0)
    timeout = int(srv.get("request_timeout_seconds") or 0)
    if not host:
        issues.append(HandoffIssue("missing_server_host", "server.host required"))
    if port <= 0 or port > 65535:
        issues.append(HandoffIssue("invalid_server_port", f"server.port must be 1–65535, got {port}"))
    if timeout <= 0:
        issues.append(HandoffIssue("invalid_request_timeout", "server.request_timeout_seconds must be positive"))
    return (
        ServerConfig(
            host=host or "127.0.0.1",
            port=port or 8000,
            request_timeout_seconds=timeout or 30,
        ),
        issues,
    )


def load_validation_limits(config: Mapping[str, Any]) -> tuple[ValidationLimits, list[HandoffIssue]]:
    issues: list[HandoffIssue] = []
    val = dict(config.get("validation") or {})
    max_body = int(val.get("max_request_body_bytes") or 0)
    max_query = int(val.get("max_query_length") or 0)
    max_session = int(val.get("max_session_id_length") or 0)
    content_type = str(val.get("required_content_type") or "").strip()
    if max_body <= 0:
        issues.append(HandoffIssue("invalid_max_body", "validation.max_request_body_bytes must be positive"))
    if max_query <= 0:
        issues.append(HandoffIssue("invalid_max_query", "validation.max_query_length must be positive"))
    if max_session <= 0:
        issues.append(HandoffIssue("invalid_max_session", "validation.max_session_id_length must be positive"))
    if not content_type:
        issues.append(HandoffIssue("missing_content_type", "validation.required_content_type required"))
    return (
        ValidationLimits(
            max_request_body_bytes=max_body or 16384,
            max_query_length=max_query or 2000,
            max_session_id_length=max_session or 128,
            required_content_type=content_type or "application/json",
        ),
        issues,
    )


def load_cors_config(config: Mapping[str, Any]) -> CorsConfig:
    cors = dict(config.get("cors") or {})
    return CorsConfig(
        dev_origins=[str(x) for x in (cors.get("dev_origins") or [])],
        prod_origins=[str(x) for x in (cors.get("prod_origins") or [])],
    )


def load_logging_config(config: Mapping[str, Any]) -> LoggingConfig:
    log_cfg = dict(config.get("logging") or {})
    return LoggingConfig(
        level=str(log_cfg.get("level") or "INFO"),
        redact_pii=bool(log_cfg.get("redact_pii", True)),
        redact_field_names=[str(x) for x in (log_cfg.get("redact_field_names") or [])],
    )


def validate_phase6_generation_handoff(handoff: dict[str, Any]) -> list[HandoffIssue]:
    issues: list[HandoffIssue] = []
    if str(handoff.get("phase")) != "5.6":
        issues.append(HandoffIssue("handoff_phase", f"expected phase 5.6, got {handoff.get('phase')!r}"))

    api = handoff.get("api_surface") or {}
    if not str(api.get("answer") or ""):
        issues.append(HandoffIssue("missing_api_answer", "api_surface.answer"))

    envelope = api.get("answer_envelope") or {}
    fields = envelope.get("fields") or []
    if not isinstance(fields, list) or not fields:
        issues.append(HandoffIssue("missing_envelope_fields", "api_surface.answer_envelope.fields"))
    else:
        required = {
            "outcome_type",
            "query",
            "validation_passed",
            "assistant",
            "display_text",
        }
        missing = required - {str(f) for f in fields}
        if missing:
            issues.append(
                HandoffIssue(
                    "incomplete_envelope_fields",
                    f"missing: {sorted(missing)}",
                ),
            )

    outcome_types = envelope.get("outcome_types") or []
    if not outcome_types:
        issues.append(HandoffIssue("missing_outcome_types", "api_surface.answer_envelope.outcome_types"))

    chat = api.get("chat_endpoint_suggestion") or {}
    if str(chat.get("path") or "") != "/chat":
        issues.append(HandoffIssue("chat_path", f"expected /chat, got {chat.get('path')!r}"))
    body = chat.get("request_body") or {}
    if "query" not in body:
        issues.append(HandoffIssue("missing_chat_query_field", "chat_endpoint_suggestion.request_body.query"))

    hooks = handoff.get("middleware_hooks") or {}
    for key in ("pre_generation", "post_generation"):
        hook = hooks.get(key) or {}
        if not str(hook.get("module") or ""):
            issues.append(HandoffIssue(f"missing_{key}_module", f"middleware_hooks.{key}.module"))

    eval_summary = handoff.get("evaluation_summary") or {}
    if eval_summary.get("passed") is not True:
        issues.append(
            HandoffIssue(
                "warning_eval_not_passed",
                "evaluation_summary.passed is not true — run Phase 5.6 --eval-full",
            ),
        )

    return issues


def build_phase6_handoff_context(config: Mapping[str, Any]) -> Phase6HandoffContext:
    issues: list[HandoffIssue] = []
    phase5 = Phase5HandoffPaths.from_config(config)
    handoff_path = phase5.phase6_generation_handoff_path(config)

    handoff = _read_json(handoff_path)
    if handoff is None:
        issues.append(HandoffIssue("missing_phase6_handoff", str(handoff_path)))
        handoff = {}
    elif handoff:
        for issue in validate_phase6_generation_handoff(handoff):
            if issue.code.startswith("warning_"):
                issues.append(issue)
            else:
                issues.append(issue)

    server, srv_issues = load_server_config(config)
    issues.extend(srv_issues)

    validation, val_issues = load_validation_limits(config)
    issues.extend(val_issues)

    cors = load_cors_config(config)
    logging_cfg = load_logging_config(config)

    api = handoff.get("api_surface") or {}
    chat = api.get("chat_endpoint_suggestion") or {}
    envelope = api.get("answer_envelope") or {}

    return Phase6HandoffContext(
        phase6_handoff=handoff,
        handoff_path=handoff_path,
        server=server,
        validation=validation,
        cors=cors,
        logging=logging_cfg,
        chat_endpoint_path=str(chat.get("path") or "/chat"),
        answer_envelope_fields=[str(f) for f in (envelope.get("fields") or [])],
        outcome_types=[str(t) for t in (envelope.get("outcome_types") or [])],
        issues=issues,
    )


def workspace_layout_ok(api_ui_root: Path) -> list[HandoffIssue]:
    """Confirm Phase 6 directory scaffold exists."""
    issues: list[HandoffIssue] = []
    for name in ("config", "api", "ui", "artifacts", "tests"):
        path = api_ui_root / name
        if not path.exists():
            issues.append(HandoffIssue("missing_workspace_dir", str(path)))
    config_file = api_ui_root / "config" / "api.defaults.json"
    if not config_file.is_file():
        issues.append(HandoffIssue("missing_api_defaults", str(config_file)))
    return issues
