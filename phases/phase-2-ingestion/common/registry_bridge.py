"""Load Phase 1 `source_registry` and validate with `allowlist` (no copy of URLs)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, Callable


def phases_dir() -> Path:
    """``phases/`` (sibling of ``phase-1-corpus-registry``)."""
    # common/registry_bridge.py -> parents[2] == phases
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
    """Return (validate_registry_integrity, load_registry) from Phase 1."""
    mod = _load_allowlist_module()
    return mod.validate_registry_integrity, mod.load_registry


def validate_registry_or_raise() -> dict[str, Any]:
    """Load `source_registry.json` via Phase 1 and run integrity checks."""
    validate, load = get_allowlist_validators()
    registry_path = phase1_corpus_dir() / "source_registry.json"
    data = load(registry_path)
    validate(data)
    return data


def canonicalize_url(url: str) -> str:
    """Delegate to Phase 1 allowlist URL canonicalization."""
    mod = _load_allowlist_module()
    return mod.canonicalize_url(url)


def is_allowlisted_url(url: str) -> bool:
    mod = _load_allowlist_module()
    return mod.is_allowlisted(url)
