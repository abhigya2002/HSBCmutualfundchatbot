"""Embedding provider interface."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Mapping


class EmbeddingProvider(ABC):
    @property
    @abstractmethod
    def model_id(self) -> str:
        ...

    @property
    @abstractmethod
    def dimensions(self) -> int:
        ...

    @abstractmethod
    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        """Batch-embed texts; return one vector per text."""


def get_provider(config: Mapping[str, Any]) -> EmbeddingProvider:
    emb = config.get("embedding") or {}
    provider_name = str(emb.get("provider", "hash_v1")).lower()
    if provider_name == "hash_v1":
        from phase_3_4.providers.hash_v1 import HashEmbeddingV1

        return HashEmbeddingV1(
            model_id=str(emb.get("model_id", "hash-embedding-v1")),
            dimensions=int(emb.get("dimensions", 384)),
        )
    if provider_name == "openai":
        from phase_3_4.providers.openai_provider import OpenAIEmbeddingProvider

        return OpenAIEmbeddingProvider(
            model_id=str(emb.get("model_id", "text-embedding-3-small")),
            dimensions=int(emb.get("dimensions", 1536)),
        )
    raise ValueError(f"Unknown embedding provider: {provider_name!r}")
