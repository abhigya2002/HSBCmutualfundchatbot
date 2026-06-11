"""Build ``index_version`` identifiers (P3-10)."""

from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone
from typing import Any, Mapping


def _slug_model(model_id: str) -> str:
    s = re.sub(r"[^a-zA-Z0-9]+", "-", model_id.lower()).strip("-")
    return s[:48] or "model"


def build_index_version(
    *,
    embedding_model_id: str,
    chunk_count: int,
    config: Mapping[str, Any],
    explicit: str | None = None,
) -> str:
    if explicit:
        return explicit
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    cfg_hash = hashlib.sha256(
        repr(
            {
                "model": embedding_model_id,
                "provider": (config.get("embedding") or {}).get("provider"),
                "dims": (config.get("embedding") or {}).get("dimensions"),
                "chunks": chunk_count,
            },
        ).encode("utf-8"),
    ).hexdigest()[:10]
    return f"idx_{ts}_{_slug_model(embedding_model_id)}_{cfg_hash}"
