"""Single-URL ingestion pipeline: raw → processed → index manifest."""

from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

from mf_faq.ingestion.config import (
    HTTP_HEADERS,
    HTTP_TIMEOUT,
    INDEX_DIR,
    MANIFEST_PATH,
    PROCESSED_DIR,
    RAW_DIR,
    REDIRECT_STATUS_CODES,
)
from mf_faq.ingestion.sources import SourceEntry, load_sources
from mf_faq.ingestion.stable_hash import stable_content_hash

log = logging.getLogger(__name__)


class Pipeline:
    """Re-run ingestion and indexing for one allowlisted Groww scheme URL."""

    def refresh_url(self, url: str) -> None:
        entry = self._entry_for_url(url)
        log.info("pipeline_refresh_start scheme=%s", entry.scheme)
        html = self._fetch_raw(entry)
        RAW_DIR.mkdir(parents=True, exist_ok=True)
        raw_path = RAW_DIR / f"{entry.scheme}.html"
        raw_path.write_text(html, encoding="utf-8")

        processed = self._extract_processed(html, entry)
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        processed_path = PROCESSED_DIR / f"{entry.scheme}.json"
        processed_path.write_text(json.dumps(processed, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")

        self._update_index(entry, processed)
        log.info("pipeline_refresh_done scheme=%s", entry.scheme)

    def _entry_for_url(self, url: str) -> SourceEntry:
        normalized = url.strip().rstrip("/")
        for entry in load_sources():
            if entry.url == normalized:
                return entry
        raise ValueError(f"URL not in config/sources.yaml: {url}")

    def _fetch_raw(self, entry: SourceEntry) -> str:
        with httpx.Client(timeout=HTTP_TIMEOUT, follow_redirects=False, headers=HTTP_HEADERS) as client:
            resp = client.get(entry.url)
        if resp.status_code in REDIRECT_STATUS_CODES:
            raise RuntimeError(f"Redirect detected for {entry.url} (status {resp.status_code})")
        if resp.status_code == 404:
            raise RuntimeError(f"404 for {entry.url}")
        if resp.status_code != 200:
            raise RuntimeError(f"HTTP {resp.status_code} for {entry.url}")
        return resp.text

    def _extract_processed(self, html: str, entry: SourceEntry) -> dict:
        soup = BeautifulSoup(html, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.decompose()
        text = soup.get_text("\n", strip=True)
        content_hash = stable_content_hash(text)
        return {
            "scheme": entry.scheme,
            "source_url": entry.url,
            "processed_at": datetime.now(timezone.utc).isoformat(),
            "content_hash": content_hash,
            "text_length": len(text),
            "body_text": text[:500_000],
        }

    def _update_index(self, entry: SourceEntry, processed: dict) -> None:
        INDEX_DIR.mkdir(parents=True, exist_ok=True)
        index_record_path = INDEX_DIR / f"{entry.scheme}.json"
        index_record = {
            "scheme": entry.scheme,
            "source_url": entry.url,
            "content_hash": processed["content_hash"],
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "text_length": processed["text_length"],
        }
        index_record_path.write_text(json.dumps(index_record, indent=2) + "\n", encoding="utf-8")

        manifest = self._load_manifest()
        manifest["updated_at"] = datetime.now(timezone.utc).isoformat()
        schemes = manifest.setdefault("schemes", {})
        schemes[entry.scheme] = {
            "url": entry.url,
            "indexed_at": index_record["indexed_at"],
            "content_hash": processed["content_hash"],
            "index_record": index_record_path.name,
        }
        MANIFEST_PATH.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    def _load_manifest(self) -> dict:
        if MANIFEST_PATH.is_file():
            return json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
        return {"manifest_version": "1.0.0", "updated_at": None, "schemes": {}}
