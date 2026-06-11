"""Build searchable index from Phase 1 source registry (16 schemes)."""

from __future__ import annotations

import re
from dataclasses import dataclass, field

from phase_4_1.registry_bridge import canonicalize_url, validate_registry_or_raise

_SUFFIX_RE = re.compile(
    r"\s*\((?:direct\s+)?growth\)\s*$",
    flags=re.IGNORECASE,
)
_WS = re.compile(r"\s+")
_STRIP_TOKENS = frozenset(
    {"hsbc", "fund", "funds", "mutual", "direct", "growth", "the", "and", "of", "a", "an"},
)


@dataclass(frozen=True)
class SchemeRecord:
    scheme: str
    url: str
    display_name: str
    core_phrase: str
    slug_spaced: str
    distinctive_tokens: tuple[str, ...]


@dataclass
class RegistryIndex:
    records: list[SchemeRecord] = field(default_factory=list)
    by_scheme: dict[str, SchemeRecord] = field(default_factory=dict)
    default_citation_url: str = ""

    @classmethod
    def from_registry(
        cls,
        registry: dict | None = None,
        *,
        default_url: str = "",
    ) -> "RegistryIndex":
        data = registry or validate_registry_or_raise()
        idx = cls(default_citation_url=default_url)
        for entry in data.get("entries") or []:
            scheme = str(entry.get("scheme") or "").strip()
            url = canonicalize_url(str(entry.get("url") or ""))
            display = str(entry.get("scheme_display_name") or scheme)
            if not scheme or not url:
                continue
            rec = _make_record(scheme, url, display)
            idx.records.append(rec)
            idx.by_scheme[scheme] = rec
        return idx

    def slugs(self) -> list[str]:
        return [r.scheme for r in self.records]


def _normalize_text(text: str) -> str:
    t = text.lower().strip()
    t = t.replace("\u2019", "'").replace("\u2018", "'")
    t = t.replace("-", " ")
    return _WS.sub(" ", t)


def _core_phrase_from_slug(scheme: str) -> str:
    s = scheme
    if s.startswith("hsbc-"):
        s = s[5:]
    for suffix in ("-direct-growth", "-direct-growth-plan"):
        if s.endswith(suffix):
            s = s[: -len(suffix)]
    return _normalize_text(s.replace("-", " "))


def _display_core(display_name: str) -> str:
    d = _SUFFIX_RE.sub("", display_name.strip())
    return _normalize_text(d)


def _distinctive_tokens(core: str) -> tuple[str, ...]:
    toks = [t for t in core.split() if t and t not in _STRIP_TOKENS]
    return tuple(toks)


def _make_record(scheme: str, url: str, display_name: str) -> SchemeRecord:
    core = _core_phrase_from_slug(scheme)
    disp = _display_core(display_name)
    # Prefer longer display core when it adds tokens (e.g. "large and mid cap")
    if len(disp) > len(core):
        core = disp.replace("hsbc ", "").strip() if disp.startswith("hsbc ") else disp
    return SchemeRecord(
        scheme=scheme,
        url=url,
        display_name=display_name,
        core_phrase=core,
        slug_spaced=_normalize_text(scheme),
        distinctive_tokens=_distinctive_tokens(core),
    )
