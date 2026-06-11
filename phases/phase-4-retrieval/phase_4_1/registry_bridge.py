"""Phase 1 registry + allowlist (Phase 4 retrieval gates)."""

from __future__ import annotations

import importlib.util
from pathlib import Path
from types import ModuleType
from typing import Any, Callable, FrozenSet


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


def validate_registry_or_raise() -> dict[str, Any]:
    mod = _load_allowlist_module()
    registry_path = phase1_corpus_dir() / "source_registry.json"
    data = mod.load_registry(registry_path)
    mod.validate_registry_integrity(data)
    return data


def allowlisted_urls_set() -> FrozenSet[str]:
    mod = _load_allowlist_module()
    return mod.allowlisted_urls_set()


def canonicalize_url(url: str) -> str:
    mod = _load_allowlist_module()
    return mod.canonicalize_url(url)


def is_allowlisted_url(url: str) -> bool:
    mod = _load_allowlist_module()
    return mod.is_allowlisted(url)
