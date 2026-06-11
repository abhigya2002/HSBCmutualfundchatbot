"""Project paths and HTTP defaults for mf_faq ingestion."""

from __future__ import annotations

from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = PROJECT_ROOT / "config"
SOURCES_YAML = CONFIG_DIR / "sources.yaml"
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
INDEX_DIR = DATA_DIR / "index"
REFRESH_DIR = DATA_DIR / "refresh"
CONTENT_HASHES_PATH = REFRESH_DIR / "content_hashes.json"
MANIFEST_PATH = INDEX_DIR / "manifest.json"

HTTP_TIMEOUT = 30.0
DRIFT_THRESHOLD = 3

BROWSER_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
)
HTTP_HEADERS = {"User-Agent": BROWSER_USER_AGENT}

REDIRECT_STATUS_CODES = frozenset({301, 302, 303, 307, 308})
