"""Phase 3.4 embedding and vector index paths."""

from __future__ import annotations

from pathlib import Path

from phase_3_1.paths import Phase3ArtifactPaths


def index_version_dir_name(index_version: str) -> str:
    safe = index_version.replace("/", "_").replace("\\", "_")
    return safe


def embeddings_version_dir(phase3: Phase3ArtifactPaths, index_version: str) -> Path:
    return phase3.embeddings / index_version_dir_name(index_version)


def vector_index_version_dir(phase3: Phase3ArtifactPaths, index_version: str) -> Path:
    return phase3.indexes / "vector" / index_version_dir_name(index_version)


def vector_active_pointer_path(phase3: Phase3ArtifactPaths) -> Path:
    return phase3.indexes / "vector" / "active.json"


def embedding_manifest_path(emb_dir: Path) -> Path:
    return emb_dir / "embedding_manifest.json"


def vectors_store_path(emb_dir: Path) -> Path:
    return emb_dir / "vectors.json"


def chunk_records_path(index_dir: Path) -> Path:
    return index_dir / "chunk_records.json"


def vector_index_manifest_path(index_dir: Path) -> Path:
    return index_dir / "vector_index_manifest.json"
