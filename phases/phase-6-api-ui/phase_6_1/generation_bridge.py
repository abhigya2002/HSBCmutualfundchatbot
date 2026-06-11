"""Import Phase 5.6 ``GenerationService`` without duplicating generation logic."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase_6_1.config_load import resolve_phase5_guardrails_root


@dataclass(frozen=True)
class GenerationServiceProbe:
    guardrails_root: Path
    service_class: str
    instantiated: bool
    error: str = ""


def ensure_phase5_on_path(config: dict[str, Any]) -> Path:
    guardrails_root = resolve_phase5_guardrails_root(config)
    path_str = str(guardrails_root)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)
    return guardrails_root


def probe_generation_service(config: dict[str, Any]) -> GenerationServiceProbe:
    guardrails_root = ensure_phase5_on_path(config)
    try:
        from phase_5_6.service import GenerationService

        GenerationService()
        return GenerationServiceProbe(
            guardrails_root=guardrails_root,
            service_class="phase_5_6.service.GenerationService",
            instantiated=True,
        )
    except Exception as exc:
        return GenerationServiceProbe(
            guardrails_root=guardrails_root,
            service_class="phase_5_6.service.GenerationService",
            instantiated=False,
            error=str(exc),
        )
