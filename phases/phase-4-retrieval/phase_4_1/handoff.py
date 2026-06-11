"""Load and validate Phase 3 index handoff for retrieval."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from phase_4_1.paths import Phase3Paths
from phase_4_1.registry_bridge import allowlisted_urls_set, canonicalize_url, validate_registry_or_raise


@dataclass
class HandoffIssue:
    code: str
    message: str


@dataclass
class IndexHandoffContext:
    index_version: str
    embedding_model_id: str
    vector_index_dir: Path
    keyword_index_dir: Path
    bm25_index_path: Path
    chunk_records_path: Path
    embeddings_dir: Path | None
    vector_chunk_count: int
    keyword_chunk_count: int
    bm25_document_count: int
    registry_entry_count: int
    hybrid_contract: dict[str, Any]
    phase4_handoff: dict[str, Any]
    issues: list[HandoffIssue] = field(default_factory=list)

    @property
    def ready(self) -> bool:
        return not any(
            i.code.startswith("error_") or i.code in ("missing_vector_active", "missing_keyword_active")
            for i in self.issues
        )


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _resolve_existing(path_str: str, fallbacks: list[Path]) -> Path | None:
    if not path_str:
        return None
    p = Path(path_str)
    if p.is_file() or p.is_dir():
        return p.resolve()
    for base in fallbacks:
        candidate = (base / path_str).resolve()
        if candidate.is_file() or candidate.is_dir():
            return candidate
    return None


def load_handoff_documents(phase3: Phase3Paths) -> tuple[dict[str, Any] | None, dict[str, Any] | None, list[HandoffIssue]]:
    issues: list[HandoffIssue] = []
    handoff = _read_json(phase3.phase4_handoff_path())
    if handoff is None:
        issues.append(HandoffIssue("missing_phase4_handoff", str(phase3.phase4_handoff_path())))
    contract = _read_json(phase3.hybrid_contract_path())
    if contract is None:
        issues.append(HandoffIssue("missing_hybrid_contract", str(phase3.hybrid_contract_path())))
    return handoff, contract, issues


def validate_registry_handoff() -> tuple[dict[str, Any], list[HandoffIssue]]:
    issues: list[HandoffIssue] = []
    try:
        registry = validate_registry_or_raise()
    except Exception as exc:
        issues.append(HandoffIssue("registry_invalid", str(exc)))
        return {}, issues
    entries = registry.get("entries") or []
    if len(entries) != 16:
        issues.append(HandoffIssue("registry_count", f"expected 16 entries, got {len(entries)}"))
    return registry, issues


def build_index_handoff_context(config: Mapping[str, Any]) -> IndexHandoffContext:
    phase3 = Phase3Paths.from_config(config)
    issues: list[HandoffIssue] = []

    handoff, contract, doc_issues = load_handoff_documents(phase3)
    issues.extend(doc_issues)
    registry, reg_issues = validate_registry_handoff()
    issues.extend(reg_issues)

    vector_active = _read_json(phase3.vector_active_path())
    keyword_active = _read_json(phase3.keyword_active_path())

    if vector_active is None:
        issues.append(HandoffIssue("missing_vector_active", str(phase3.vector_active_path())))
    if keyword_active is None:
        issues.append(HandoffIssue("missing_keyword_active", str(phase3.keyword_active_path())))

    index_version = ""
    embedding_model_id = ""
    vector_dir: Path | None = None
    keyword_dir: Path | None = None
    bm25_path: Path | None = None
    embeddings_dir: Path | None = None
    vector_chunk_count = 0
    keyword_chunk_count = 0
    bm25_docs = 0

    chunking_fb = [phase3.chunking_artifacts]
    indexing_fb = [phase3.indexing_artifacts]

    if vector_active:
        index_version = str(vector_active.get("index_version") or "")
        embedding_model_id = str(vector_active.get("embedding_model_id") or "")
        vector_chunk_count = int(vector_active.get("chunk_count") or 0)
        vdir = _resolve_existing(str(vector_active.get("vector_index_dir") or ""), chunking_fb)
        if vdir is None:
            issues.append(HandoffIssue("missing_vector_index_dir", "vector_index_dir not found"))
        else:
            vector_dir = vdir
        edir = vector_active.get("embeddings_dir")
        if edir:
            embeddings_dir = _resolve_existing(str(edir), chunking_fb)

    if keyword_active:
        keyword_chunk_count = int(keyword_active.get("chunk_count") or 0)
        kdir = _resolve_existing(str(keyword_active.get("keyword_index_dir") or ""), indexing_fb)
        if kdir is None:
            issues.append(HandoffIssue("missing_keyword_index_dir", "keyword_index_dir not found"))
        else:
            keyword_dir = kdir
        bm25_path = _resolve_existing(str(keyword_active.get("bm25_index_path") or ""), indexing_fb)
        if bm25_path is None and keyword_dir:
            candidate = keyword_dir / "bm25_index.json"
            if candidate.is_file():
                bm25_path = candidate
        if bm25_path is None:
            issues.append(HandoffIssue("missing_bm25_index", "bm25_index.json not found"))

    if vector_active and keyword_active:
        v_ver = str(vector_active.get("index_version") or "")
        k_ver = str(keyword_active.get("index_version") or "")
        if v_ver and k_ver and v_ver != k_ver:
            issues.append(HandoffIssue("index_version_mismatch", f"vector={v_ver!r} keyword={k_ver!r}"))
        if not index_version:
            index_version = v_ver or k_ver

    chunk_records_path = (vector_dir / "chunk_records.json") if vector_dir else Path()
    records_count = 0
    allowlist = allowlisted_urls_set()
    if chunk_records_path.is_file():
        rows = json.loads(chunk_records_path.read_text(encoding="utf-8"))
        if isinstance(rows, list):
            records_count = len(rows)
            for row in rows[:5]:  # sample check; full scan below if small
                if not isinstance(row, dict):
                    continue
            if records_count <= 500:
                for row in rows:
                    if not isinstance(row, dict):
                        continue
                    url = str(row.get("source_url") or "")
                    try:
                        if canonicalize_url(url) not in allowlist:
                            issues.append(
                                HandoffIssue("chunk_url_not_allowlisted", f"{row.get('chunk_id')}: {url}"),
                            )
                            break
                    except Exception:
                        issues.append(HandoffIssue("chunk_url_invalid", str(row.get("chunk_id"))))
                        break
    elif vector_dir:
        issues.append(HandoffIssue("missing_chunk_records", str(chunk_records_path)))

    if bm25_path and bm25_path.is_file():
        bm25_data = json.loads(bm25_path.read_text(encoding="utf-8"))
        bm25_docs = int(bm25_data.get("n_docs") or len(bm25_data.get("docs") or {}))

    if vector_chunk_count and records_count and vector_chunk_count != records_count:
        issues.append(
            HandoffIssue(
                "chunk_count_mismatch",
                f"active={vector_chunk_count} records={records_count}",
            ),
        )
    if keyword_chunk_count and bm25_docs and keyword_chunk_count != bm25_docs:
        issues.append(
            HandoffIssue(
                "bm25_count_mismatch",
                f"active={keyword_chunk_count} bm25={bm25_docs}",
            ),
        )

    manifest = _read_json(phase3.phase3_index_manifest_path())
    if manifest and index_version:
        if str(manifest.get("index_version")) != index_version:
            issues.append(HandoffIssue("manifest_version_mismatch", "phase3_index_manifest index_version"))

    return IndexHandoffContext(
        index_version=index_version,
        embedding_model_id=embedding_model_id,
        vector_index_dir=vector_dir or Path(),
        keyword_index_dir=keyword_dir or Path(),
        bm25_index_path=bm25_path or Path(),
        chunk_records_path=chunk_records_path,
        embeddings_dir=embeddings_dir,
        vector_chunk_count=vector_chunk_count or records_count,
        keyword_chunk_count=keyword_chunk_count or bm25_docs,
        bm25_document_count=bm25_docs,
        registry_entry_count=len(registry.get("entries") or []),
        hybrid_contract=contract or {},
        phase4_handoff=handoff or {},
        issues=issues,
    )
