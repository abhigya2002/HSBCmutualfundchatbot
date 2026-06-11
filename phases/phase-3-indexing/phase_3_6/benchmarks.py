"""Load retrieval benchmark set."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class BenchmarkQuery:
    id: str
    intent: str
    query: str
    scheme: str
    expected_source_url: str
    expected_chunk_id: str | None = None

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "BenchmarkQuery":
        return cls(
            id=str(d["id"]),
            intent=str(d.get("intent") or ""),
            query=str(d["query"]),
            scheme=str(d.get("scheme") or ""),
            expected_source_url=str(d.get("expected_source_url") or ""),
            expected_chunk_id=str(d["expected_chunk_id"]) if d.get("expected_chunk_id") else None,
        )


def load_benchmark(path: Path | None = None) -> list[BenchmarkQuery]:
    from phase_3_6.paths import default_benchmark_path

    p = path or default_benchmark_path()
    data = json.loads(p.read_text(encoding="utf-8"))
    rows = data.get("queries") or []
    return [BenchmarkQuery.from_dict(r) for r in rows if isinstance(r, dict)]
