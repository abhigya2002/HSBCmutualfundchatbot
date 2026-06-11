"""Load Phase 3.3 validated chunk bundles for embedding."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from phase_3_1.paths import Phase3ArtifactPaths
from phase_3_3.paths import phase3_validated_manifest_path, validated_chunk_bundle_path


@dataclass(frozen=True)
class ChunkRecord:
    chunk_id: str
    text: str
    source_url: str
    scheme: str
    doc_type: str
    section_title: str
    effective_date: str | None
    compliance_rank: int
    metadata: dict[str, Any]

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "ChunkRecord":
        return cls(
            chunk_id=str(d["chunk_id"]),
            text=str(d.get("text") or ""),
            source_url=str(d.get("source_url") or ""),
            scheme=str(d.get("scheme") or ""),
            doc_type=str(d.get("doc_type") or ""),
            section_title=str(d.get("section_title") or ""),
            effective_date=str(d["effective_date"]) if d.get("effective_date") else None,
            compliance_rank=int(d.get("compliance_rank", 1)),
            metadata={
                k: v
                for k, v in d.items()
                if k
                not in {
                    "chunk_id",
                    "text",
                    "source_url",
                    "scheme",
                    "doc_type",
                    "section_title",
                    "effective_date",
                    "compliance_rank",
                }
            },
        )


@dataclass(frozen=True)
class ValidatedBundle:
    scheme: str
    source_url: str
    path: Path
    indexable: bool
    chunks: list[ChunkRecord]


def load_validated_bundle(path: Path) -> ValidatedBundle:
    data = json.loads(path.read_text(encoding="utf-8"))
    scheme = str(data.get("scheme") or path.stem.replace(".chunks", ""))
    chunks_raw = data.get("chunks") or []
    chunks = [ChunkRecord.from_dict(c) for c in chunks_raw if isinstance(c, dict)]
    return ValidatedBundle(
        scheme=scheme,
        source_url=str(data.get("source_url") or ""),
        path=path,
        indexable=bool(data.get("indexable", True)),
        chunks=chunks,
    )


def load_indexable_chunks(phase3: Phase3ArtifactPaths) -> list[ChunkRecord]:
    """Load all chunks from validated manifest or ``chunks_validated/`` glob."""
    manifest_path = phase3_validated_manifest_path(phase3)
    records: list[ChunkRecord] = []

    if manifest_path.is_file():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        for entry in manifest.get("entries") or []:
            if not entry.get("indexable"):
                continue
            scheme = str(entry.get("scheme") or "")
            path = Path(str(entry.get("validated_bundle_path") or ""))
            if not path.is_file():
                path = validated_chunk_bundle_path(phase3, scheme)
            if path.is_file():
                records.extend(load_validated_bundle(path).chunks)
        if records:
            return records

    for path in sorted(phase3.chunks_validated.glob("*.chunks.json")):
        bundle = load_validated_bundle(path)
        if bundle.indexable and bundle.chunks:
            records.extend(bundle.chunks)
    return records
