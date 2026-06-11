"""Load Phase 2 ``clean_document`` + Markdown body for chunking."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping

from phase_3_1.paths import Phase2ArtifactPaths


@dataclass(frozen=True)
class SchemeChunkInput:
    scheme: str
    source_url: str
    body: str
    body_sha256: str
    clean_document: dict[str, Any]
    doc_metadata: dict[str, Any]
    body_sha256_expected: str | None = None
    sha256_mismatch: bool = False


def _read_json(path: Path) -> dict[str, Any]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError(f"Expected JSON object at {path}")
    return data


def _sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def resolve_markdown_path(phase2: Phase2ArtifactPaths, scheme: str) -> Path:
    """Canonical Markdown per Phase 2 handoff: ``artifacts/clean/{slug}.md``."""
    return phase2.clean_markdown_path(scheme)


def effective_date_from_metadata(doc_metadata: Mapping[str, Any], clean_document: Mapping[str, Any]) -> str | None:
    for key in ("published_date", "fetched_at"):
        val = doc_metadata.get(key)
        if val:
            return str(val)
    upstream = clean_document.get("status_upstream") or {}
    fetched = upstream.get("fetched_at")
    return str(fetched) if fetched else None


def load_scheme_chunk_input(
    scheme: str,
    registry_url: str,
    phase2: Phase2ArtifactPaths,
    *,
    strict_sha256: bool = False,
) -> SchemeChunkInput:
    clean_doc_path = phase2.clean_document_path(scheme)
    meta_path = phase2.doc_metadata_path(scheme)
    clean_document = _read_json(clean_doc_path)
    doc_metadata = _read_json(meta_path)

    md_path = resolve_markdown_path(phase2, scheme)
    if not md_path.is_file():
        raise FileNotFoundError(f"Missing Markdown body: {md_path}")
    body = md_path.read_text(encoding="utf-8")
    body_sha = _sha256_text(body)

    expected = str(clean_document.get("body_sha256") or doc_metadata.get("content_sha256") or "") or None
    mismatch = bool(expected and expected != body_sha)
    if mismatch and strict_sha256:
        raise ValueError(
            f"body_sha256 mismatch for {scheme}: expected={expected!r} actual={body_sha!r} "
            f"(re-run Phase 2.6 finalize or pass without --strict-sha256)",
        )

    source_url = str(clean_document.get("source_url") or doc_metadata.get("source_url") or registry_url)
    return SchemeChunkInput(
        scheme=scheme,
        source_url=source_url,
        body=body,
        body_sha256=body_sha,
        clean_document=clean_document,
        doc_metadata=doc_metadata,
        body_sha256_expected=expected,
        sha256_mismatch=mismatch,
    )
