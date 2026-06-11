"""Optional OpenAI embeddings (requires ``OPENAI_API_KEY``)."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any


class OpenAIEmbeddingProvider:
    def __init__(self, *, model_id: str, dimensions: int) -> None:
        self._model_id = model_id
        self._dimensions = dimensions

    @property
    def model_id(self) -> str:
        return self._model_id

    @property
    def dimensions(self) -> int:
        return self._dimensions

    def embed_texts(self, texts: list[str]) -> list[list[float]]:
        api_key = os.environ.get("OPENAI_API_KEY", "").strip()
        if not api_key:
            raise RuntimeError("OPENAI_API_KEY is not set")
        out: list[list[float]] = []
        batch_size = 64
        for i in range(0, len(texts), batch_size):
            batch = texts[i : i + batch_size]
            payload: dict[str, Any] = {"model": self._model_id, "input": batch}
            if "text-embedding-3" in self._model_id:
                payload["dimensions"] = self._dimensions
            req = urllib.request.Request(
                "https://api.openai.com/v1/embeddings",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=120) as resp:
                    body = json.loads(resp.read().decode("utf-8"))
            except urllib.error.HTTPError as exc:
                detail = exc.read().decode("utf-8", errors="replace")
                raise RuntimeError(f"OpenAI embeddings failed: {exc.code} {detail}") from exc
            rows = sorted(body.get("data") or [], key=lambda r: int(r.get("index", 0)))
            for row in rows:
                vec = row.get("embedding")
                if not isinstance(vec, list):
                    raise RuntimeError("Invalid embedding response")
                out.append([float(x) for x in vec])
        return out
