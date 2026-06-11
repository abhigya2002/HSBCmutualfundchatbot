"""Project-root ``.env`` and read-only Groq status from Phase 5.4."""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

from dotenv import load_dotenv

from phase_6_1.config_load import project_root


@dataclass(frozen=True)
class GroqEnvStatus:
    dotenv_path: Path
    dotenv_found: bool
    use_groq: str
    api_key_configured: bool
    groq_composer_enabled: bool
    note: str


@lru_cache(maxsize=1)
def load_project_env() -> Path:
    dotenv_path = project_root() / ".env"
    if dotenv_path.is_file():
        load_dotenv(dotenv_path=dotenv_path, override=False)
    return dotenv_path


def probe_groq_status(*, phase5_on_path: bool) -> GroqEnvStatus:
    """Report Groq feature-flag state without duplicating Phase 5.4 composer logic."""
    dotenv_path = load_project_env()
    use_groq = os.environ.get("USE_GROQ", "").strip()
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    api_key_configured = bool(api_key) and api_key != "your_groq_api_key_here"

    enabled = False
    note = "Phase 5.4 env_config not loaded"
    if phase5_on_path:
        try:
            from phase_5_4.env_config import groq_composer_enabled

            enabled = groq_composer_enabled()
            note = "Delegated to phase_5_4.env_config.groq_composer_enabled()"
        except ImportError as exc:
            note = f"Could not import phase_5_4.env_config: {exc}"

    return GroqEnvStatus(
        dotenv_path=dotenv_path,
        dotenv_found=dotenv_path.is_file(),
        use_groq=use_groq,
        api_key_configured=api_key_configured,
        groq_composer_enabled=enabled,
        note=note,
    )
