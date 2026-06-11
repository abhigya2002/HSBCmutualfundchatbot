"""Optional Groq LLM wording for factual answers (Phase 5.4)."""

from __future__ import annotations

import logging
import os

from groq import Groq

from phase_5_4.env_config import load_env

log = logging.getLogger("phase5_guardrails.phase_5_4.groq_composer")

GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_TEMPERATURE = 0.1
GROQ_MAX_TOKENS = 200

SYSTEM_PROMPT = (
    "You are a facts-only mutual fund assistant. Using ONLY the "
    "provided source text, write a factual answer in maximum 3 "
    "sentences. Do not add any information not present in the source "
    "text. Do not give advice or recommendations."
)


def compose_body_with_groq(
    *,
    query: str,
    chunk_text: str,
    max_sentences: int = 3,
    performance_limited: bool = False,
) -> str:
    """Reword retrieved chunk text via Groq; raises on API failure."""
    load_env()
    api_key = os.environ.get("GROQ_API_KEY", "").strip()
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is not set")

    user_parts = [
        f"User question: {query.strip()}",
        "",
        "Source text:",
        chunk_text.strip(),
        "",
        f"Write at most {max_sentences} sentence(s). Use only facts from the source text.",
    ]
    if performance_limited:
        user_parts.append(
            "This is a performance-related question. State only what the source says; do not project returns.",
        )

    client = Groq(api_key=api_key)
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": "\n".join(user_parts)},
        ],
        temperature=GROQ_TEMPERATURE,
        max_tokens=GROQ_MAX_TOKENS,
    )
    content = response.choices[0].message.content
    if not content or not content.strip():
        raise RuntimeError("Groq returned empty completion")
    body = content.strip()
    log.debug("Groq composed body (%d chars) for query=%r", len(body), query[:80])
    return body
