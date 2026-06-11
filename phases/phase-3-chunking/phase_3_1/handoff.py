"""Validate Phase 2 outputs required before chunking (Phase 3.1)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Mapping

from phase_3_1.paths import Phase2ArtifactPaths
from phase_3_1.registry_bridge import canonicalize_url, is_allowlisted_url


@dataclass
class SchemeHandoffResult:
    scheme: str
    source_url: str
    indexable: bool
    blockers: list[str] = field(default_factory=list)
    extract_status: str | None = None
    normalize_status: str | None = None
    quarantined: bool = False
    paths: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "scheme": self.scheme,
            "source_url": self.source_url,
            "indexable": self.indexable,
            "blockers": list(self.blockers),
            "extract_status": self.extract_status,
            "normalize_status": self.normalize_status,
            "quarantined": self.quarantined,
            "paths": dict(self.paths),
        }


def _handoff_rules(config: Mapping[str, Any]) -> tuple[frozenset[str], frozenset[str], frozenset[str]]:
    handoff = config.get("handoff") or {}
    indexable = frozenset(str(x) for x in (handoff.get("indexable_extract_statuses") or ("ok", "partial")))
    blocked_ex = frozenset(str(x) for x in (handoff.get("blocked_extract_statuses") or ("parse_error", "empty_shell")))
    blocked_ns = frozenset(str(x) for x in (handoff.get("blocked_normalize_statuses") or ("empty", "failed")))
    return indexable, blocked_ex, blocked_ns


def _read_json(path: Path) -> dict[str, Any] | None:
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None
    return data if isinstance(data, dict) else None


def _load_phase2_manifest(paths: Phase2ArtifactPaths) -> dict[str, Any] | None:
    return _read_json(paths.phase2_corpus_manifest_path())


def _manifest_entry_for_scheme(manifest: dict[str, Any] | None, scheme: str) -> dict[str, Any] | None:
    if not manifest:
        return None
    for row in manifest.get("entries") or []:
        if isinstance(row, dict) and str(row.get("scheme")) == scheme:
            return row
    return None


def validate_scheme_handoff(
    scheme: str,
    registry_url: str,
    phase2: Phase2ArtifactPaths,
    config: Mapping[str, Any],
    *,
    manifest: dict[str, Any] | None = None,
) -> SchemeHandoffResult:
    """
    Assert ``clean_document``, Markdown body, and ``doc_metadata`` exist and are
  acceptable for indexing. Does not chunk or embed.
    """
    indexable_statuses, blocked_extract, blocked_normalize = _handoff_rules(config)
    blockers: list[str] = []
    result_paths: dict[str, str] = {}

    clean_doc_path = phase2.clean_document_path(scheme)
    md_path = phase2.clean_markdown_path(scheme)
    meta_path = phase2.doc_metadata_path(scheme)
    result_paths["clean_document"] = str(clean_doc_path)
    result_paths["clean_markdown"] = str(md_path)
    result_paths["doc_metadata"] = str(meta_path)

    manifest_row = _manifest_entry_for_scheme(manifest, scheme)
    quarantined = bool(manifest_row.get("quarantined")) if manifest_row else phase2.quarantine_review_path(scheme).is_file()

    clean_doc = _read_json(clean_doc_path)
    doc_meta = _read_json(meta_path)

    extract_status: str | None = None
    normalize_status: str | None = None
    source_url = registry_url

    if not clean_doc_path.is_file():
        blockers.append("missing_clean_document")
    if not md_path.is_file():
        blockers.append("missing_clean_markdown")
    elif md_path.stat().st_size == 0:
        blockers.append("empty_clean_markdown")
    if not meta_path.is_file():
        blockers.append("missing_doc_metadata")

    if quarantined:
        blockers.append("quarantined")

    if clean_doc:
        upstream = clean_doc.get("status_upstream") or {}
        extract_status = str(upstream.get("extract_status") or clean_doc.get("extract_status") or "")
        normalize_status = str(upstream.get("normalize_status") or "") or None
        doc_url = str(clean_doc.get("source_url") or "")
        if doc_url:
            source_url = doc_url
        body_path = clean_doc.get("body_markdown_path")
        if body_path:
            result_paths["body_markdown_resolved"] = str(Path(str(body_path)).resolve())
            if not Path(str(body_path)).is_file():
                blockers.append("clean_document_body_markdown_missing")
        sections = clean_doc.get("sections")
        if sections is None:
            blockers.append("clean_document_missing_sections")
        elif not isinstance(sections, list):
            blockers.append("clean_document_sections_invalid")
    else:
        blockers.append("clean_document_unreadable")

    if doc_meta:
        extract_status = extract_status or str(doc_meta.get("extract_status") or "")
        normalize_status = normalize_status or str(doc_meta.get("normalize_status") or "") or None
        meta_url = str(doc_meta.get("source_url") or "")
        if meta_url:
            source_url = meta_url
    elif "missing_doc_metadata" not in blockers:
        blockers.append("doc_metadata_unreadable")

    if extract_status:
        if extract_status in blocked_extract:
            blockers.append(f"extract_status={extract_status}")
        elif extract_status not in indexable_statuses:
            blockers.append(f"extract_status_not_indexable={extract_status}")
    else:
        blockers.append("extract_status_missing")

    if normalize_status and normalize_status in blocked_normalize:
        blockers.append(f"normalize_status={normalize_status}")

    try:
        if not is_allowlisted_url(source_url):
            blockers.append("source_url_not_allowlisted")
        elif canonicalize_url(source_url) != canonicalize_url(registry_url):
            blockers.append("source_url_registry_mismatch")
    except Exception:
        blockers.append("source_url_invalid")

    indexable = len(blockers) == 0
    return SchemeHandoffResult(
        scheme=scheme,
        source_url=source_url,
        indexable=indexable,
        blockers=blockers,
        extract_status=extract_status or None,
        normalize_status=normalize_status,
        quarantined=quarantined,
        paths=result_paths,
    )


def validate_all_schemes(
    entries: list[Mapping[str, Any]],
    phase2: Phase2ArtifactPaths,
    config: Mapping[str, Any],
) -> list[SchemeHandoffResult]:
    manifest = _load_phase2_manifest(phase2)
    results: list[SchemeHandoffResult] = []
    for e in sorted(entries, key=lambda x: int(x["id"])):
        scheme = str(e["scheme"])
        url = str(e["url"])
        results.append(
            validate_scheme_handoff(scheme, url, phase2, config, manifest=manifest),
        )
    return results
