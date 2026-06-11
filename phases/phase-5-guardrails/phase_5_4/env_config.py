"""Load project-root ``.env`` and Groq feature flags for Phase 5.4."""

from __future__ import annotations

import os
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

_PLACEHOLDER_KEY = "your_groq_api_key_here"


def project_root() -> Path:
    return Path(__file__).resolve().parents[3]


@lru_cache(maxsize=1)
def load_env() -> None:
    load_dotenv(dotenv_path=Path(__file__).resolve().parents[3] / ".env")


def groq_composer_enabled() -> bool:
    """True when ``USE_GROQ=true`` and a non-placeholder ``GROQ_API_KEY`` is set."""
    load_env()
    use_groq = os.environ.get("USE_GROQ", "").strip().lower()
    if use_groq not in ("true", "1", "yes"):
        return False
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key or api_key == _PLACEHOLDER_KEY:
        return False
    return True
