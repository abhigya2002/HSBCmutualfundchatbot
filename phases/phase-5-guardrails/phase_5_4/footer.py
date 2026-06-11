"""Footer date formatting for factual answers (P5-05)."""

from __future__ import annotations

from datetime import datetime

from phase_5_1.handoff import ComposerDefaults


def _parse_effective_date(raw: str) -> datetime | None:
    text = (raw or "").strip()
    if not text:
        return None
    normalized = text.replace("Z", "+00:00")
    try:
        return datetime.fromisoformat(normalized)
    except ValueError:
        pass
    for fmt in ("%d %b %Y", "%Y-%m-%d", "%d-%m-%Y"):
        try:
            return datetime.strptime(text, fmt)
        except ValueError:
            continue
    return None


def resolve_footer_date(effective_date: str, composer: ComposerDefaults) -> tuple[str, str]:
    """
    Return (footer_date, footer_line).

    Never invent a date — use configured unavailable copy when metadata is missing.
    """
    parsed = _parse_effective_date(effective_date)
    if parsed is None:
        unavailable = composer.footer_date_unavailable
        return unavailable, composer.footer_template.format(date=unavailable)
    display = parsed.strftime("%d %b %Y")
    return display, composer.footer_template.format(date=display)
