"""Deterministic local embeddings (no API key) for dev and tests."""

from __future__ import annotations

import hashlib
import math
import re
from typing import Sequence


class HashEmbeddingV1:
    """
    Hash-trick bag-of-tokens vectors, L2-normalized.

    Not semantically equivalent to neural embeddings; suitable for pipeline
    integration and offline CI. Swap ``embedding.provider`` to ``openai`` in prod.
    """

    def __init__(self, *, model_id: str = "hash-embedding-v1", dimensions: int = 384) -> None:
        if dimensions < 8:
            raise ValueError("dimensions must be >= 8")
        self._model_id = model_id
        self._dimensions = dimensions

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        return [self._embed_one(t) for t in texts]

    def _embed_one(self, text: str) -> list[float]:
        dim = self._dimensions
        vec = [0.0] * dim
        tokens = re.findall(r"[a-z0-9%]+", text.lower())
        if not tokens:
            tokens = ["_empty_"]
        for i, token in enumerate(tokens):
            digest = hashlib.sha256(f"{self._model_id}:{i}:{token}".encode("utf-8")).digest()
            for b in range(min(16, len(digest))):
                idx = digest[b] % dim
                sign = 1.0 if digest[(b + 7) % len(digest)] % 2 == 0 else -1.0
                vec[idx] += sign
        norm = math.sqrt(sum(x * x for x in vec)) or 1.0
        return [x / norm for x in vec]
