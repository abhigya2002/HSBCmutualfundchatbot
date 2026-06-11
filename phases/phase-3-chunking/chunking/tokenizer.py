"""Token *estimates* for budgeting (no model tokenizer required in v1)."""


def estimate_tokens(text: str, *, chars_per_token: float = 4.0) -> int:
    """Rough English-ish budget: characters / chars_per_token."""
    if chars_per_token <= 0:
        raise ValueError("chars_per_token must be positive")
    return max(1, int(len(text) / chars_per_token))
