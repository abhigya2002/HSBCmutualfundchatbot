"""Assemble ``doc_metadata`` records from Phase 2.2–2.4 artifacts."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Mapping

from phase_2_3.extract import EXTRACT_VERSION as PARSER_VERSION_DEFAULT
from phase_2_4.normalize import NORMALIZER_VERSION as NORMALIZER_VERSION_DEFAULT
from phase_2_5.candidates import extract_all_candidates

METADATA_BUILDER_VERSION = "2.5.0"


def _read_json(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def build_doc_metadata(
    *,
    scheme: str,
    source_url: str,
    clean_md_path: Path,
    raw_html_path: Path,
    crawl_path: Path,
    extract_path: Path,
    normalize_path: Path,
    metadata_out_path: Path,
    registry_entry: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """
    Build one ``doc_metadata`` object and write ``metadata_out_path``.

    Missing optional sidecars leave corresponding fields ``null`` where noted.
    """
    crawl = _read_json(crawl_path)
    extract = _read_json(extract_path)
    normalize = _read_json(normalize_path)

    if not clean_md_path.exists():
        rec: dict[str, Any] = {
            "scheme": scheme,
            "source_url": source_url,
            "content_sha256": None,
            "parser_version": extract.get("parser_version") or PARSER_VERSION_DEFAULT,
            "fetched_at": crawl.get("fetched_at_utc"),
            "extract_status": extract.get("extract_status"),
            "normalizer_version": normalize.get("normalizer_version") or NORMALIZER_VERSION_DEFAULT,
            "normalize_status": normalize.get("normalize_status"),
            "metadata_builder_version": METADATA_BUILDER_VERSION,
            "error": "missing_clean_markdown",
            "artifact_paths": {
                "raw_html": str(raw_html_path),
                "clean_markdown": str(clean_md_path),
                "extract_sidecar": str(extract_path),
                "normalize_sidecar": str(normalize_path),
                "doc_metadata": str(metadata_out_path),
            },
            "candidates": {
                "expense_ratio": None,
                "exit_load": None,
                "min_sip": None,
                "lock_in": None,
                "riskometer": None,
                "benchmark": None,
                "statement_tax": None,
            },
        }
        if registry_entry is not None:
            rec["registry"] = {"id": registry_entry.get("id"), "scheme": registry_entry.get("scheme")}
        metadata_out_path.parent.mkdir(parents=True, exist_ok=True)
        metadata_out_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
        return rec

    md_bytes = clean_md_path.read_bytes()
    sha = hashlib.sha256(md_bytes).hexdigest()
    text = md_bytes.decode("utf-8", errors="replace")

    parser_version = extract.get("parser_version") or PARSER_VERSION_DEFAULT
    normalizer_version = normalize.get("normalizer_version") or NORMALIZER_VERSION_DEFAULT
    fetched_at = crawl.get("fetched_at_utc")
    extract_status = extract.get("extract_status")
    normalize_status = normalize.get("normalize_status")

    candidates = extract_all_candidates(text)

    rec = {
        "scheme": scheme,
        "source_url": source_url,
        "content_sha256": sha,
        "parser_version": parser_version,
        "fetched_at": fetched_at,
        "extract_status": extract_status,
        "normalizer_version": normalizer_version,
        "normalize_status": normalize_status,
        "metadata_builder_version": METADATA_BUILDER_VERSION,
        "candidates_note": "Best-effort regex on normalized Markdown; not QA-verified facts.",
        "artifact_paths": {
            "raw_html": str(raw_html_path),
            "clean_markdown": str(clean_md_path),
            "extract_sidecar": str(extract_path),
            "normalize_sidecar": str(normalize_path),
            "doc_metadata": str(metadata_out_path),
        },
        "candidates": candidates,
    }
    if registry_entry is not None:
        rec["registry"] = {"id": registry_entry.get("id"), "scheme": registry_entry.get("scheme")}
    metadata_out_path.parent.mkdir(parents=True, exist_ok=True)
    metadata_out_path.write_text(json.dumps(rec, indent=2), encoding="utf-8")
    return rec
