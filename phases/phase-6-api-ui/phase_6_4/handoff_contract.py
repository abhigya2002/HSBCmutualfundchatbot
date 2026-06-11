"""Load and validate contracts from ``phase6_generation_handoff.json``."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from phase_6_1.config_load import load_config, phase6_api_ui_root
from phase_6_1.paths import Phase5HandoffPaths


@dataclass
class ContractIssue:
    code: str
    message: str


@dataclass
class HandoffContract:
    handoff_path: Path
    handoff: dict[str, Any]
    envelope_fields: frozenset[str]
    assistant_fields: frozenset[str]
    outcome_types: frozenset[str]
    chat_path: str
    chat_request_fields: frozenset[str]
    issues: list[ContractIssue] = field(default_factory=list)


def handoff_path_from_config(config: Mapping[str, Any] | None = None) -> Path:
    cfg = dict(config or load_config())
    return Phase5HandoffPaths.from_config(cfg).phase6_generation_handoff_path(cfg)


def load_handoff_contract(config: Mapping[str, Any] | None = None) -> HandoffContract:
    cfg = dict(config or load_config())
    path = handoff_path_from_config(cfg)
    issues: list[ContractIssue] = []

    if not path.is_file():
        issues.append(ContractIssue("missing_handoff", str(path)))
        return HandoffContract(
            handoff_path=path,
            handoff={},
            envelope_fields=frozenset(),
            assistant_fields=frozenset(),
            outcome_types=frozenset(),
            chat_path="/chat",
            chat_request_fields=frozenset(),
            issues=issues,
        )

    handoff = json.loads(path.read_text(encoding="utf-8"))
    api = handoff.get("api_surface") or {}
    envelope = api.get("answer_envelope") or {}
    assistant = api.get("assistant_response") or {}
    chat = api.get("chat_endpoint_suggestion") or {}
    request_body = chat.get("request_body") or {}

    envelope_fields = frozenset(str(f) for f in (envelope.get("fields") or []))
    assistant_fields = frozenset(str(f) for f in (assistant.get("fields") or []))
    outcome_types = frozenset(str(t) for t in (envelope.get("outcome_types") or []))
    chat_path = str(chat.get("path") or "/chat")
    chat_request_fields = frozenset(str(k) for k in request_body.keys())

    if str(handoff.get("phase")) != "5.6":
        issues.append(ContractIssue("handoff_phase", f"expected 5.6, got {handoff.get('phase')!r}"))
    if not envelope_fields:
        issues.append(ContractIssue("missing_envelope_fields", "api_surface.answer_envelope.fields"))
    if not assistant_fields:
        issues.append(ContractIssue("missing_assistant_fields", "api_surface.assistant_response.fields"))
    if not outcome_types:
        issues.append(ContractIssue("missing_outcome_types", "api_surface.answer_envelope.outcome_types"))

    return HandoffContract(
        handoff_path=path,
        handoff=handoff,
        envelope_fields=envelope_fields,
        assistant_fields=assistant_fields,
        outcome_types=outcome_types,
        chat_path=chat_path,
        chat_request_fields=chat_request_fields,
        issues=issues,
    )


def validate_envelope_against_handoff(
    envelope: Mapping[str, Any],
    contract: HandoffContract | None = None,
) -> list[ContractIssue]:
    c = contract or load_handoff_contract()
    issues: list[ContractIssue] = []
    keys = set(envelope.keys())
    missing = c.envelope_fields - keys
    if missing:
        issues.append(ContractIssue("envelope_field_missing", f"missing {sorted(missing)}"))
    extra = keys - c.envelope_fields
    if extra:
        issues.append(ContractIssue("envelope_field_extra", f"unexpected {sorted(extra)}"))
    outcome = str(envelope.get("outcome_type") or "")
    if c.outcome_types and outcome not in c.outcome_types:
        issues.append(ContractIssue("invalid_outcome_type", outcome))
    assistant = envelope.get("assistant")
    if isinstance(assistant, dict):
        a_missing = c.assistant_fields - set(assistant.keys())
        if a_missing:
            issues.append(ContractIssue("assistant_field_missing", f"missing {sorted(a_missing)}"))
    return issues
