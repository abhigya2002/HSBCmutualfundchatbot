"""Load allowlisted sources from config/sources.yaml."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import yaml

from mf_faq.ingestion.config import SOURCES_YAML

EXPECTED_SOURCE_COUNT = 16


@dataclass(frozen=True)
class SourceEntry:
    scheme: str
    url: str


def load_sources(path: Path | None = None) -> tuple[SourceEntry, ...]:
    p = path or SOURCES_YAML
    if not p.is_file():
        raise FileNotFoundError(f"Source registry not found: {p}")

    data = yaml.safe_load(p.read_text(encoding="utf-8")) or {}
    raw_sources = data.get("sources") or []
    if not isinstance(raw_sources, list):
        raise ValueError("sources.yaml: 'sources' must be a list")

    entries: list[SourceEntry] = []
    seen_urls: set[str] = set()
    for item in raw_sources:
        if not isinstance(item, dict):
            continue
        scheme = str(item.get("scheme") or "").strip()
        url = str(item.get("url") or "").strip().rstrip("/")
        if not scheme or not url:
            raise ValueError(f"sources.yaml: invalid entry (scheme/url required): {item!r}")
        if url in seen_urls:
            raise ValueError(f"sources.yaml: duplicate URL: {url}")
        seen_urls.add(url)
        entries.append(SourceEntry(scheme=scheme, url=url))

    if len(entries) != EXPECTED_SOURCE_COUNT:
        raise ValueError(
            f"sources.yaml: expected {EXPECTED_SOURCE_COUNT} sources, found {len(entries)}"
        )
    return tuple(entries)


def url_for_scheme(scheme: str, entries: tuple[SourceEntry, ...] | None = None) -> str:
    src = entries or load_sources()
    for entry in src:
        if entry.scheme == scheme:
            return entry.url
    raise KeyError(f"Scheme not in sources.yaml: {scheme}")
