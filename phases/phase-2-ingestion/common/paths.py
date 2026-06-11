"""Artifact directory layout for raw, clean, and metadata stores."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class ArtifactPaths:
    """Resolved paths under the Phase 2 ingestion workspace."""

    root: Path
    raw: Path
    clean: Path
    metadata: Path
    extracted: Path
    quarantine: Path

    @classmethod
    def from_config(cls, config: Mapping[str, Any], phase2_root: Path) -> "ArtifactPaths":
        rel_root = Path(str(config.get("artifact_root", "artifacts")))
        root = rel_root if rel_root.is_absolute() else (phase2_root / rel_root).resolve()
        dirs = config.get("directories") or {}
        raw_name = str(dirs.get("raw", "raw"))
        clean_name = str(dirs.get("clean", "clean"))
        meta_name = str(dirs.get("metadata", "metadata"))
        extracted_name = str(dirs.get("extracted", "extracted"))
        return cls(
            root=root,
            raw=(root / raw_name).resolve(),
            clean=(root / clean_name).resolve(),
            metadata=(root / meta_name).resolve(),
            extracted=(root / extracted_name).resolve(),
            quarantine=(root / "quarantine").resolve(),
        )

    def ensure_dirs(self) -> None:
        """Create raw, clean, metadata, extracted, and quarantine directories (idempotent)."""
        self.raw.mkdir(parents=True, exist_ok=True)
        self.clean.mkdir(parents=True, exist_ok=True)
        self.metadata.mkdir(parents=True, exist_ok=True)
        self.extracted.mkdir(parents=True, exist_ok=True)
        self.quarantine.mkdir(parents=True, exist_ok=True)

    def planned_raw_path(self, scheme_slug: str) -> Path:
        """Raw HTML snapshot path (Phase 2.2)."""
        return self.raw / f"{self._slug_fs(scheme_slug)}.html"

    def _slug_fs(self, scheme_slug: str) -> str:
        return scheme_slug.replace("/", "_")

    def planned_clean_path(self, scheme_slug: str) -> Path:
        """Normalized Markdown for chunking (Phase 2.4+)."""
        return self.clean / f"{self._slug_fs(scheme_slug)}.md"

    def normalize_sidecar_path(self, scheme_slug: str) -> Path:
        return self.clean / f"{self._slug_fs(scheme_slug)}.normalize.json"

    def planned_metadata_path(self, scheme_slug: str) -> Path:
        """Per-scheme ``doc_metadata`` JSON (Phase 2.5+)."""
        return self.metadata / f"{self._slug_fs(scheme_slug)}.json"

    def raw_html_path(self, scheme_slug: str) -> Path:
        return self.planned_raw_path(scheme_slug)

    def crawl_meta_path(self, scheme_slug: str) -> Path:
        return self.raw / f"{self._slug_fs(scheme_slug)}.crawl.json"

    def extracted_main_html_path(self, scheme_slug: str) -> Path:
        return self.extracted / f"{self._slug_fs(scheme_slug)}.main.html"

    def extract_sidecar_path(self, scheme_slug: str) -> Path:
        return self.extracted / f"{self._slug_fs(scheme_slug)}.extract.json"

    def clean_document_path(self, scheme_slug: str) -> Path:
        """Final ``clean_document`` JSON: Markdown path + section offsets (Phase 2.6)."""
        return self.clean / f"{self._slug_fs(scheme_slug)}.clean.json"

    def quarantine_review_path(self, scheme_slug: str) -> Path:
        return self.quarantine / f"{self._slug_fs(scheme_slug)}.review.json"

    def phase2_corpus_manifest_path(self) -> Path:
        return self.root / "phase2_corpus_manifest.json"

    def phase2_quality_report_path(self) -> Path:
        return self.root / "phase2_quality_report.json"
