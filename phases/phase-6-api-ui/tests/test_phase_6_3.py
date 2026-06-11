"""Tests for Phase 6.3 /chat generation integration."""

from __future__ import annotations

import unittest
from dataclasses import dataclass
from typing import Any

from fastapi.testclient import TestClient
from starlette.requests import Request

from phase_6_1.config_load import load_config
from phase_6_1.generation_bridge import ensure_phase5_on_path
from phase_6_2.app import create_app
from phase_6_2.readiness import assess_readiness
from phase_6_3.envelope import envelope_to_json, validate_envelope_shape
from phase_6_3.handler import ChatHandler
from phase_6_3.service_bridge import reset_generation_service_cache

ensure_phase5_on_path(load_config())
from phase_5_1.registry_bridge import is_allowlisted_url

GILT_URL = "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth"
DEFAULT_URL = "https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth"


@dataclass
class _FakeAssistant:
    display_text: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "answer_type": "factual",
            "body_text": "The expense ratio is 0.48%.",
            "citation_url": GILT_URL,
            "citation_markdown": f"[HSBC Gilt Fund]({GILT_URL})",
            "footer_line": "Last updated from sources: May 2026",
            "footer_date": "May 2026",
            "disclaimer_line": "Facts-only. No investment advice.",
            "display_text": self.display_text,
            "evidence_chunk_id": "test_chunk",
            "refusal_type": "",
            "validation_passed": True,
            "validation_repaired": False,
        }


@dataclass
class _FakeEnvelope:
    outcome_type: str
    query: str
    session_id: str
    retrieval_outcome_type: str
    compliance_decision: str
    compliance_reasons: list[str]
    validation_passed: bool
    validation_repaired: bool
    assistant: dict[str, Any]
    display_text: str
    audit: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {
            "outcome_type": self.outcome_type,
            "query": self.query,
            "session_id": self.session_id,
            "retrieval_outcome_type": self.retrieval_outcome_type,
            "compliance_decision": self.compliance_decision,
            "compliance_reasons": self.compliance_reasons,
            "validation_passed": self.validation_passed,
            "validation_repaired": self.validation_repaired,
            "assistant": self.assistant,
            "display_text": self.display_text,
            "audit": self.audit,
        }


class _FakeGenerationService:
    def __init__(self, envelope: _FakeEnvelope) -> None:
        self._envelope = envelope
        self.last_request: Any = None

    def answer(self, request: Any) -> _FakeEnvelope:
        self.last_request = request
        return self._envelope


def _fake_factual_envelope(query: str = "expense ratio HSBC Gilt") -> _FakeEnvelope:
    assistant = _FakeAssistant(
        display_text=(
            f"The expense ratio is 0.48%. [HSBC Gilt Fund]({GILT_URL})\n\n"
            "Last updated from sources: May 2026\n\nFacts-only. No investment advice."
        ),
    )
    return _FakeEnvelope(
        outcome_type="factual",
        query=query,
        session_id="",
        retrieval_outcome_type="retrieval",
        compliance_decision="allow_compose",
        compliance_reasons=["retrieval_evidence_present"],
        validation_passed=True,
        validation_repaired=False,
        assistant=assistant.to_dict(),
        display_text=assistant.display_text,
        audit={"composer_route": "factual"},
    )


def _fake_refusal_envelope(query: str = "Should I buy HSBC Gilt?") -> _FakeEnvelope:
    assistant = {
        "answer_type": "refusal",
        "body_text": "I cannot provide investment advice.",
        "citation_url": GILT_URL,
        "citation_markdown": f"[HSBC Gilt Fund]({GILT_URL})",
        "footer_line": "",
        "footer_date": "",
        "disclaimer_line": "Facts-only. No investment advice.",
        "display_text": "I cannot provide investment advice.",
        "evidence_chunk_id": "",
        "refusal_type": "advisory",
        "validation_passed": True,
        "validation_repaired": False,
    }
    return _FakeEnvelope(
        outcome_type="refusal",
        query=query,
        session_id="",
        retrieval_outcome_type="refusal",
        compliance_decision="refuse",
        compliance_reasons=["advisory_intent"],
        validation_passed=True,
        validation_repaired=False,
        assistant=assistant,
        display_text=str(assistant["display_text"]),
        audit={"refusal_type": "advisory", "hybrid_skipped": True},
    )


class TestEnvelopeShape(unittest.TestCase):
    def test_envelope_to_json_validates_fields(self) -> None:
        data = envelope_to_json(_fake_factual_envelope())
        validate_envelope_shape(data)
        self.assertEqual(data["outcome_type"], "factual")


class TestChatHandler(unittest.TestCase):
    def test_handler_returns_envelope(self) -> None:
        fake = _FakeGenerationService(_fake_factual_envelope())
        handler = ChatHandler(config=load_config(), service_factory=lambda: fake)

        scope = {
            "type": "http",
            "method": "POST",
            "path": "/chat",
            "headers": [],
        }
        request = Request(scope)
        request.state.validated_payload = {"query": "expense ratio HSBC Gilt"}

        import asyncio

        response = asyncio.run(handler.handle(request))
        self.assertEqual(response.status_code, 200)
        body = response.body.decode()
        self.assertIn("outcome_type", body)
        self.assertIn("factual", body)

    def test_handler_maps_runtime_error_to_503(self) -> None:
        class _BrokenService:
            def answer(self, request: Any) -> None:
                raise RuntimeError("indexes missing")

        handler = ChatHandler(config=load_config(), service_factory=lambda: _BrokenService())
        request = Request({"type": "http", "method": "POST", "path": "/chat", "headers": []})
        request.state.validated_payload = {"query": "hello"}

        import asyncio

        response = asyncio.run(handler.handle(request))
        self.assertEqual(response.status_code, 503)
        self.assertEqual(response.body.decode().count("indexes missing"), 0)


class TestChatIntegration(unittest.TestCase):
    def setUp(self) -> None:
        reset_generation_service_cache()
        self.cfg = load_config()
        self.ready = assess_readiness(self.cfg).ready

    def _client_with_fake(self, fake_service: _FakeGenerationService) -> TestClient:
        app = create_app(self.cfg, service_factory=lambda: fake_service)
        return TestClient(app)

    def test_factual_mock_envelope(self) -> None:
        fake = _FakeGenerationService(_fake_factual_envelope())
        client = self._client_with_fake(fake)
        resp = client.post("/chat", json={"query": "expense ratio HSBC Gilt Fund Direct Growth"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["outcome_type"], "factual")
        self.assertTrue(data["validation_passed"])
        self.assertTrue(is_allowlisted_url(data["assistant"]["citation_url"]))

    def test_refusal_mock_envelope(self) -> None:
        fake = _FakeGenerationService(_fake_refusal_envelope())
        client = self._client_with_fake(fake)
        resp = client.post("/chat", json={"query": "Should I buy HSBC Gilt Fund?"})
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["outcome_type"], "refusal")
        self.assertEqual(data["assistant"]["refusal_type"], "advisory")

    def test_live_factual_query(self) -> None:
        if not self.ready:
            self.skipTest("indexes or GenerationService not ready")
        client = TestClient(create_app(self.cfg))
        resp = client.post(
            "/chat",
            json={"query": "expense ratio HSBC Gilt Fund Direct Growth"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        validate_envelope_shape(data)
        self.assertEqual(data["outcome_type"], "factual")
        self.assertTrue(is_allowlisted_url(data["assistant"]["citation_url"]))

    def test_live_advisory_refusal(self) -> None:
        if not self.ready:
            self.skipTest("indexes or GenerationService not ready")
        client = TestClient(create_app(self.cfg))
        resp = client.post(
            "/chat",
            json={"query": "Should I buy HSBC Gilt Fund?"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["outcome_type"], "refusal")

    def test_live_abstention_or_factual_vague_query(self) -> None:
        if not self.ready:
            self.skipTest("indexes or GenerationService not ready")
        client = TestClient(create_app(self.cfg))
        resp = client.post(
            "/chat",
            json={"query": "what is the expense ratio"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data["outcome_type"], ("abstention", "factual", "refusal"))
        if data["outcome_type"] == "abstention":
            url = str(data["assistant"].get("citation_url") or "")
            if url:
                self.assertTrue(is_allowlisted_url(url))


if __name__ == "__main__":
    unittest.main()
