"""Live /chat client for Phase 7.1 metrics."""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import Any

import httpx


@dataclass
class ChatCallResult:
    query: str
    status_code: int
    latency_ms: int
    envelope: dict[str, Any] | None
    error: str | None = None

    @property
    def ok(self) -> bool:
        return self.status_code == 200 and isinstance(self.envelope, dict)


class ChatClient:
    def __init__(self, base_url: str, *, timeout_seconds: float = 60.0) -> None:
        self.base_url = base_url.rstrip("/")
        self.timeout_seconds = timeout_seconds
        self._client = httpx.Client(base_url=self.base_url, timeout=timeout_seconds)

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> ChatClient:
        return self

    def __exit__(self, *args: object) -> None:
        self.close()

    def health_ok(self) -> bool:
        try:
            r = self._client.get("/health")
            return r.status_code == 200 and r.json().get("status") == "ok"
        except Exception:
            return False

    def chat(self, query: str) -> ChatCallResult:
        start = time.perf_counter()
        try:
            resp = self._client.post(
                "/chat",
                json={"query": query},
                headers={"Content-Type": "application/json"},
            )
            latency = int((time.perf_counter() - start) * 1000)
            try:
                body = resp.json()
            except Exception:
                body = None
            if not isinstance(body, dict):
                return ChatCallResult(
                    query=query,
                    status_code=resp.status_code,
                    latency_ms=latency,
                    envelope=None,
                    error="invalid_json",
                )
            return ChatCallResult(
                query=query,
                status_code=resp.status_code,
                latency_ms=latency,
                envelope=body,
            )
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            return ChatCallResult(
                query=query,
                status_code=0,
                latency_ms=latency,
                envelope=None,
                error=str(exc),
            )
