"""Shared ``index_version`` for Phase 3.2–3.5 pipeline runs."""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


def config_fingerprint(chunking_config: Mapping[str, Any], indexing_config: Mapping[str, Any]) -> str:
    payload = json.dumps(
        {"chunking": chunking_config, "indexing": indexing_config},
        sort_keys=True,
        default=str,
    )
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]


def build_corpus_index_version(
    chunking_config: Mapping[str, Any],
    indexing_config: Mapping[str, Any],
    *,
    explicit: str | None = None,
) -> str:
    if explicit:
        return explicit
    emb = chunking_config.get("embedding") or {}
    model = str(emb.get("model_id", "embedding"))
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    fp = config_fingerprint(chunking_config, indexing_config)
    slug = model.replace("_", "-")[:32]
    return f"idx_{ts}_{slug}_{fp}"
