"""Bridge to Phase 5.6 ``GenerationService``."""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from phase_6_3 import import_paths as _import_paths  # noqa: F401, E402

from functools import lru_cache
from typing import Any

from phase_6_1.config_load import load_config


@lru_cache(maxsize=1)
def create_generation_service(config_key: str = "default") -> Any:
    """Instantiate ``GenerationService`` using Phase 5 guardrails config."""
    _ = config_key
    _import_paths.ensure_project_import_paths()
    cfg = load_config()
    from phase_5_1.config_load import load_config as load_guardrails_config
    from phase_5_6.service import GenerationService

    return GenerationService(config=load_guardrails_config())


def reset_generation_service_cache() -> None:
    create_generation_service.cache_clear()
