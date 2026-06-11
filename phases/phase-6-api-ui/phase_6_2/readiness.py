"""Readiness checks for Phase 6.2 (indexes + GenerationService)."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from phase_6_1.config_load import phase6_api_ui_root, resolve_phase5_guardrails_root
from phase_6_1.generation_bridge import probe_generation_service


@dataclass
class ReadinessCheck:
    name: str
    ok: bool
    detail: str = ""


@dataclass
class ReadinessReport:
    ready: bool
    checks: list[ReadinessCheck] = field(default_factory=list)


def _resolve_root(config: Mapping[str, Any], key: str, default: str) -> Path:
    rel = Path(str(config.get(key) or default))
    return rel if rel.is_absolute() else (phase6_api_ui_root() / rel).resolve()


def assess_readiness(config: Mapping[str, Any]) -> ReadinessReport:
    checks: list[ReadinessCheck] = []

    chunking = _resolve_root(config, "phase3_chunking_root", "../phase-3-chunking")
    indexing = _resolve_root(config, "phase3_indexing_root", "../phase-3-indexing")
    vector_active = chunking / "artifacts" / "indexes" / "vector" / "active.json"
    keyword_active = indexing / "artifacts" / "indexes" / "keyword" / "active.json"

    checks.append(
        ReadinessCheck(
            name="vector_index_active",
            ok=vector_active.is_file(),
            detail=str(vector_active),
        ),
    )
    checks.append(
        ReadinessCheck(
            name="keyword_index_active",
            ok=keyword_active.is_file(),
            detail=str(keyword_active),
        ),
    )

    guardrails = resolve_phase5_guardrails_root(dict(config))
    checks.append(
        ReadinessCheck(
            name="phase5_workspace",
            ok=guardrails.is_dir(),
            detail=str(guardrails),
        ),
    )

    gen = probe_generation_service(dict(config))
    checks.append(
        ReadinessCheck(
            name="generation_service",
            ok=gen.instantiated,
            detail=gen.error or gen.service_class,
        ),
    )

    ready = all(c.ok for c in checks)
    return ReadinessReport(ready=ready, checks=checks)
