"""Scheme resolver: map queries to one of 16 registry slugs."""

from __future__ import annotations

import difflib
import re
from dataclasses import dataclass
from typing import Any, Mapping

from phase_4_2.classifier import normalize_query
from phase_4_3.config_load import load_scheme_aliases
from phase_4_3.contracts import SchemeResolution, SchemeStatus
from phase_4_3.registry_index import RegistryIndex, _display_core

_GROWW_PATH = re.compile(
    r"https?://(?:www\.)?groww\.in/mutual-funds/([a-z0-9-]+)",
    flags=re.IGNORECASE,
)
_COMPARISON_HINT = re.compile(
    r"\b(?:compare|comparison|which is better|better than|versus|vs\.?)\b",
    flags=re.IGNORECASE,
)
_OR_SPLIT = re.compile(r"\s+(?:or|vs\.?|versus)\s+")


@dataclass
class _SchemeScore:
    scheme: str
    score: float
    method: str
    reason: str


class SchemeResolver:
    """Resolve at most one scheme slug; detect multi-scheme and typos."""

    def __init__(
        self,
        index: RegistryIndex | None = None,
        aliases_config: Mapping[str, Any] | None = None,
    ) -> None:
        cfg = dict(aliases_config or load_scheme_aliases())
        self._thresholds = dict(cfg.get("thresholds") or {})
        default_url = str(cfg.get("default_citation_url") or "")
        self.index = index or RegistryIndex.from_registry(default_url=default_url)
        if default_url and not self.index.default_citation_url:
            self.index.default_citation_url = default_url

        raw_aliases = cfg.get("aliases") or {}
        self._aliases: list[tuple[str, str]] = sorted(
            ((normalize_query(k), str(v)) for k, v in raw_aliases.items()),
            key=lambda x: len(x[0]),
            reverse=True,
        )
        self._valid_slugs = set(self.index.by_scheme.keys())

    def resolve(self, query: str) -> SchemeResolution:
        norm = normalize_query(query)
        if not norm:
            return self._unknown(norm, ["empty_query"])

        scores: dict[str, _SchemeScore] = {}

        def add(scheme: str, score: float, method: str, reason: str) -> None:
            if scheme not in self._valid_slugs:
                return
            prev = scores.get(scheme)
            if prev is None or score > prev.score:
                scores[scheme] = _SchemeScore(scheme, score, method, reason)

        # Groww URL in query
        for m in _GROWW_PATH.finditer(query):
            slug = m.group(1).lower()
            if slug in self._valid_slugs:
                add(slug, 1.0, "url", f"url:{slug}")

        # Query-side aliases (longest phrase first)
        for phrase, slug in self._aliases:
            if phrase and phrase in norm:
                add(slug, 0.96, "alias", f"alias:{phrase}")

        for rec in self.index.records:
            # Full slug (hyphen or space form)
            if rec.scheme in norm.replace(" ", "-") or rec.slug_spaced in norm:
                add(rec.scheme, 0.98, "slug", "slug_exact")

            # Display / core phrase substring
            disp = _display_core(rec.display_name)
            if len(disp) >= 8 and disp in norm:
                add(rec.scheme, 0.94, "display_name", f"display:{disp}")
            elif len(rec.core_phrase) >= 4 and rec.core_phrase in norm:
                add(rec.scheme, 0.9, "core_phrase", f"core:{rec.core_phrase}")

            # HSBC + core phrase variant
            hsbc_core = f"hsbc {rec.core_phrase}"
            if len(hsbc_core) >= 10 and hsbc_core in norm:
                add(rec.scheme, 0.93, "hsbc_core", f"hsbc_core:{rec.core_phrase}")

            # Fuzzy core phrase (typos)
            fuzzy_ratio = self._fuzzy_ratio(norm, rec.core_phrase)
            fuzzy_min = float(self._thresholds.get("fuzzy_min_ratio", 0.86))
            if fuzzy_ratio >= fuzzy_min:
                add(rec.scheme, fuzzy_ratio * 0.92, "fuzzy", f"fuzzy:{fuzzy_ratio:.3f}")

            hsbc_fuzzy = self._fuzzy_ratio(norm, f"hsbc {rec.core_phrase}")
            if hsbc_fuzzy >= fuzzy_min:
                add(rec.scheme, hsbc_fuzzy * 0.91, "fuzzy_hsbc", f"fuzzy_hsbc:{hsbc_fuzzy:.3f}")

            for token in rec.distinctive_tokens:
                if len(token) < 8:
                    continue
                best_word = self._best_word_fuzzy(norm, token)
                if best_word >= fuzzy_min:
                    add(rec.scheme, best_word * 0.89, "fuzzy_token", f"fuzzy_token:{token}:{best_word:.3f}")

        if not scores:
            return self._unknown(norm, ["no_scheme_match"])

        ranked = sorted(scores.values(), key=lambda s: (-s.score, s.scheme))
        multi_min = float(self._thresholds.get("multi_scheme_min_score", 0.72))
        strong = [s for s in ranked if s.score >= multi_min]

        if _COMPARISON_HINT.search(norm):
            mention_schemes = self._schemes_from_comparison_mentions(norm)
            if len(mention_schemes) >= 2:
                schemes = sorted(mention_schemes)
                return SchemeResolution(
                    scheme="",
                    source_url=self.index.default_citation_url,
                    confidence=round(strong[0].score if strong else 0.7, 4),
                    status=SchemeStatus.AMBIGUOUS.value,
                    reasons=["multi_scheme:P4-03", f"comparison_mentions={','.join(schemes)}"],
                    matched_schemes=schemes,
                    match_method="comparison_mentions",
                    citation_url_candidate=self.index.default_citation_url,
                )

        if len(strong) >= 2:
            schemes = [s.scheme for s in strong[:4]]
            return SchemeResolution(
                scheme="",
                source_url=self.index.default_citation_url,
                confidence=round(strong[0].score, 4),
                status=SchemeStatus.AMBIGUOUS.value,
                reasons=["multi_scheme:P4-03", f"matched={','.join(schemes)}"],
                matched_schemes=schemes,
                match_method="multi_scheme",
                citation_url_candidate=self.index.default_citation_url,
            )

        top = ranked[0]
        resolve_min = float(self._thresholds.get("resolve_min_score", 0.82))
        gap = float(self._thresholds.get("ambiguous_gap", 0.06))
        second_score = ranked[1].score if len(ranked) > 1 else 0.0

        if top.score >= resolve_min and (top.score - second_score) >= gap:
            rec = self.index.by_scheme[top.scheme]
            return SchemeResolution(
                scheme=top.scheme,
                source_url=rec.url,
                confidence=round(top.score, 4),
                status=SchemeStatus.RESOLVED.value,
                reasons=[top.reason],
                match_method=top.method,
                citation_url_candidate=rec.url,
            )

        if top.score >= multi_min:
            return SchemeResolution(
                scheme="",
                source_url=self.index.default_citation_url,
                confidence=round(top.score, 4),
                status=SchemeStatus.AMBIGUOUS.value,
                reasons=["low_confidence_or_tie:P4-05", top.reason],
                matched_schemes=[top.scheme] + ([ranked[1].scheme] if len(ranked) > 1 else []),
                match_method=top.method,
                citation_url_candidate=self.index.default_citation_url,
            )

        return self._unknown(norm, ["below_threshold", top.reason])

    def _unknown(self, _norm: str, reasons: list[str]) -> SchemeResolution:
        return SchemeResolution(
            scheme="",
            source_url=self.index.default_citation_url,
            confidence=0.0,
            status=SchemeStatus.UNKNOWN.value,
            reasons=reasons,
            match_method="none",
            citation_url_candidate=self.index.default_citation_url,
        )

    def _schemes_from_comparison_mentions(self, norm: str) -> set[str]:
        found: set[str] = set()
        parts = _OR_SPLIT.split(norm)
        if len(parts) < 2:
            return found
        for part in parts:
            part = part.strip()
            if "hsbc" not in part:
                continue
            for alias_phrase, slug in self._aliases:
                if alias_phrase in part:
                    found.add(slug)
            for rec in self.index.records:
                if rec.core_phrase in part or rec.slug_spaced in part:
                    found.add(rec.scheme)
                elif f"hsbc {rec.core_phrase}" in part:
                    found.add(rec.scheme)
        return found

    @staticmethod
    def _best_word_fuzzy(haystack: str, token: str) -> float:
        best = 0.0
        for word in haystack.split():
            if len(word) < 4:
                continue
            r = difflib.SequenceMatcher(None, token, word).ratio()
            if r > best:
                best = r
        return best

    @staticmethod
    def _fuzzy_ratio(haystack: str, needle: str) -> float:
        if not needle or not haystack:
            return 0.0
        if needle in haystack:
            return 1.0
        # Sliding window on haystack for phrase-length match
        nlen = len(needle)
        best = 0.0
        for i in range(0, max(1, len(haystack) - nlen + 1)):
            window = haystack[i : i + nlen + 8]
            r = difflib.SequenceMatcher(None, needle, window).ratio()
            if r > best:
                best = r
        return best


def resolve_scheme(query: str) -> SchemeResolution:
    return SchemeResolver().resolve(query)
