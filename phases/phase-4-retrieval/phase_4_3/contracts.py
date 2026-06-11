"""Data contracts for Phase 4.3 scheme resolution."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import Enum
from typing import Any


class SchemeStatus(str, Enum):
    RESOLVED = "resolved"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


@dataclass(frozen=True)
class SchemeResolution:
    """Architecture contract: scheme, source_url, confidence, status."""

    scheme: str
    source_url: str
    confidence: float
    status: str
    reasons: list[str] = field(default_factory=list)
    resolved_scheme: str = ""
    citation_url_candidate: str = ""
    matched_schemes: list[str] = field(default_factory=list)
    match_method: str = ""

    def __post_init__(self) -> None:
        object.__setattr__(self, "resolved_scheme", self.resolved_scheme or self.scheme)
        object.__setattr__(
            self,
            "citation_url_candidate",
            self.citation_url_candidate or self.source_url,
        )

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["multi_scheme"] = len(self.matched_schemes) >= 2
        return d

    @property
    def multi_scheme(self) -> bool:
        return len(self.matched_schemes) >= 2

    @property
    def is_resolved(self) -> bool:
        return self.status == SchemeStatus.RESOLVED.value and bool(self.scheme)
