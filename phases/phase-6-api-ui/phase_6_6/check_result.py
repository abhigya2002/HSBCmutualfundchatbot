"""Shared check result model for Phase 6.6 validation."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class CheckResult:
    check_id: str
    description: str
    query: str | None = None
    expected: str = ""
    actual: str = ""
    passed: bool = False
    latency_ms: int = 0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
