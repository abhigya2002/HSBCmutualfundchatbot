"""Write Phase 3.2 chunk bundle artifacts."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from chunking.contracts import CHUNK_STRATEGY_VERSION, Chunk
from phase_3_2 import PHASE_3_2_VERSION
from phase_3_2.load import SchemeChunkInput


def build_chunk_bundle(
    inp: SchemeChunkInput,
    chunks: list[Chunk],
    *,
    strategy: str,
    chunking_config_snapshot: dict[str, Any],
) -> dict[str, Any]:
    return {
        "phase": "3.2",
        "phase_3_2_version": PHASE_3_2_VERSION,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "scheme": inp.scheme,
        "source_url": inp.source_url,
        "body_sha256": inp.body_sha256,
        "body_sha256_expected": inp.body_sha256_expected,
        "sha256_mismatch": inp.sha256_mismatch,
        "body_char_length": len(inp.body),
        "strategy": strategy,
        "chunk_strategy_version": CHUNK_STRATEGY_VERSION,
        "chunk_count": len(chunks),
        "chunking_config_snapshot": chunking_config_snapshot,
        "chunks": [c.to_dict() for c in chunks],
    }


def write_chunk_bundle(path: Path, bundle: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(bundle, indent=2), encoding="utf-8")
