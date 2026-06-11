"""Assemble final ``clean_document`` JSON (body reference + section offsets)."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Mapping

from phase_2_5.doc_metadata import METADATA_BUILDER_VERSION
from phase_2_6.sections import markdown_heading_sections

CLEAN_DOCUMENT_VERSION = "2.6.0"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_clean_document_record(
    *,
    scheme: str,
    source_url: str,
    clean_md_path: Path,
    doc_metadata_path: Path,
    raw_html_path: Path,
    crawl_path: Path,
    extract_path: Path,
    normalize_path: Path,
    clean_document_out: Path,
) -> dict[str, Any]:
    """
    Build the persisted ``clean_document`` object (written by caller).

    If ``clean_md_path`` is missing, returns a minimal error record (caller may skip write).
    """
    meta = _read_json(doc_metadata_path)
    extract = _read_json(extract_path)
    normalize = _read_json(normalize_path)
    crawl = _read_json(crawl_path)

    if not clean_md_path.exists():
        return {
            "clean_document_version": CLEAN_DOCUMENT_VERSION,
            "scheme": scheme,
            "source_url": source_url,
            "error": "missing_clean_markdown",
            "body_markdown_path": str(clean_md_path),
            "doc_metadata_path": str(doc_metadata_path),
        }

    body = clean_md_path.read_text(encoding="utf-8", errors="replace")
    sections = markdown_heading_sections(body)
    sha = meta.get("content_sha256")

    rec: dict[str, Any] = {
        "clean_document_version": CLEAN_DOCUMENT_VERSION,
        "scheme": scheme,
        "source_url": source_url,
        "body_markdown_path": str(clean_md_path.resolve()),
        "body_char_length": len(body),
        "body_sha256": sha,
        "sections": sections,
        "section_count": len(sections),
        "pipeline_versions": {
            "parser_version": extract.get("parser_version") or meta.get("parser_version"),
            "normalizer_version": normalize.get("normalizer_version") or meta.get("normalizer_version"),
            "metadata_builder_version": meta.get("metadata_builder_version") or METADATA_BUILDER_VERSION,
            "clean_document_version": CLEAN_DOCUMENT_VERSION,
        },
        "status_upstream": {
            "extract_status": extract.get("extract_status"),
            "normalize_status": normalize.get("normalize_status"),
            "fetch_status": crawl.get("fetch_status"),
            "fetched_at": crawl.get("fetched_at_utc"),
        },
        "artifact_paths": {
            "raw_html": str(raw_html_path.resolve()),
            "crawl_json": str(crawl_path.resolve()),
            "extract_sidecar": str(extract_path.resolve()),
            "normalize_sidecar": str(normalize_path.resolve()),
            "doc_metadata": str(doc_metadata_path.resolve()),
            "clean_document": str(clean_document_out.resolve()),
        },
    }
    return rec
