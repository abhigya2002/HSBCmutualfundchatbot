"""Load Phase 1 ``source_registry`` and validate with ``allowlist`` (no copy of URLs)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


def phases_dir() -> Path:
    return Path(__file__).resolve().parents[2]


def phase1_corpus_dir() -> Path:
    return phases_dir() / "phase-1-corpus-registry"


def _load_allowlist_module() -> ModuleType:
    path = phase1_corpus_dir() / "allowlist.py"
    spec = importlib.util.spec_from_file_location("phase1_allowlist", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Cannot load spec for {path}")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def get_allowlist_validators() -> tuple[Callable[..., Any], Callable[..., Any]]:
    mod = _load_allowlist_module()
    return mod.validate_registry_integrity, mod.load_registry


def validate_registry_or_raise() -> dict[str, Any]:
    validate, load = get_allowlist_validators()
    registry_path = phase1_corpus_dir() / "source_registry.json"
    data = load(registry_path)
    validate(data)
    return data


def canonicalize_url(url: str) -> str:
    mod = _load_allowlist_module()
    return mod.canonicalize_url(url)


def is_allowlisted_url(url: str) -> bool:
    mod = _load_allowlist_module()
    return mod.is_allowlisted(url)


def require_allowlisted(url: str) -> str:
    """Return canonical URL if allowlisted; else raise."""
    mod = _load_allowlist_module()
    return mod.require_allowlisted(url)
