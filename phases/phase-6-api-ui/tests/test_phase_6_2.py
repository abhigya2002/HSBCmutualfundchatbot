"""Tests for Phase 6.2 API foundation and request validation."""

from __future__ import annotations

import json
import unittest

from fastapi.testclient import TestClient

from phase_6_1.config_load import load_config
from phase_6_1.handoff import load_validation_limits
from phase_6_2.app import create_app
from phase_6_2.readiness import assess_readiness
from phase_6_2.request_validation import (
    ValidationLimits,
    decode_json_body,
    forbidden_field_names,
    validate_chat_payload,
    validate_chat_request,
    validate_content_type,
    validate_raw_body,
)


class TestValidationUnits(unittest.TestCase):
    def setUp(self) -> None:
        cfg = load_config()
        self.limits, issues = load_validation_limits(cfg)
        self.assertEqual(len(issues), 0)
        self.forbidden = forbidden_field_names(cfg)

    def test_wrong_content_type_415(self) -> None:
        failure = validate_content_type("text/plain", self.limits)
        self.assertIsNotNone(failure)
        assert failure is not None
        self.assertEqual(failure.http_status, 415)

    def test_null_bytes_rejected(self) -> None:
        failure = validate_raw_body(b'{"query":"hi\x00there"}', self.limits)
        self.assertIsNotNone(failure)
        assert failure is not None
        self.assertEqual(failure.http_status, 400)
        self.assertEqual(failure.code, "invalid_body")

    def test_oversized_body_413(self) -> None:
        limits = ValidationLimits(
            max_request_body_bytes=32,
            max_query_length=2000,
            max_session_id_length=128,
            required_content_type="application/json",
        )
        failure = validate_raw_body(b"x" * 64, limits)
        self.assertIsNotNone(failure)
        assert failure is not None
        self.assertEqual(failure.http_status, 413)

    def test_invalid_utf8(self) -> None:
        _, failure = decode_json_body(b"\xff\xfe")
        self.assertIsNotNone(failure)
        assert failure is not None
        self.assertEqual(failure.code, "invalid_utf8")

    def test_forbidden_pan_field(self) -> None:
        failure = validate_chat_payload(
            {"query": "expense ratio", "pan": "ABCDE1234F"},
            limits=self.limits,
            forbidden=self.forbidden,
        )
        self.assertIsNotNone(failure)
        assert failure is not None
        self.assertEqual(failure.code, "forbidden_field")

    def test_query_too_long(self) -> None:
        limits = ValidationLimits(
            max_request_body_bytes=16384,
            max_query_length=10,
            max_session_id_length=128,
            required_content_type="application/json",
        )
        failure = validate_chat_payload(
            {"query": "x" * 20},
            limits=limits,
            forbidden=self.forbidden,
        )
        self.assertIsNotNone(failure)
        assert failure is not None
        self.assertEqual(failure.code, "query_too_long")

    def test_valid_payload(self) -> None:
        body = json.dumps({"query": "expense ratio HSBC Gilt", "session_id": "abc"}).encode()
        payload, failure, q_len = validate_chat_request(
            content_type="application/json",
            body=body,
            limits=self.limits,
            forbidden=self.forbidden,
        )
        self.assertIsNone(failure)
        self.assertIsNotNone(payload)
        self.assertEqual(q_len, len("expense ratio HSBC Gilt"))


class TestApiRoutes(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(load_config()))

    def test_health_ok(self) -> None:
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json().get("status"), "ok")

    def test_readiness_reports_checks(self) -> None:
        report = assess_readiness(load_config())
        resp = self.client.get("/ready")
        if report.ready:
            self.assertEqual(resp.status_code, 200)
            self.assertTrue(resp.json().get("ready"))
        else:
            self.assertEqual(resp.status_code, 503)
        self.assertIn("checks", resp.json())

    def test_chat_wrong_content_type(self) -> None:
        resp = self.client.post("/chat", content="query=hi", headers={"Content-Type": "text/plain"})
        self.assertEqual(resp.status_code, 415)
        self.assertEqual(resp.json()["error"]["code"], "unsupported_media_type")

    def test_chat_invalid_json(self) -> None:
        resp = self.client.post(
            "/chat",
            content=b"{not-json",
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "invalid_json")

    def test_chat_forbidden_field(self) -> None:
        resp = self.client.post(
            "/chat",
            json={"query": "hello", "aadhaar": "1234"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "forbidden_field")

    def test_chat_missing_query(self) -> None:
        resp = self.client.post("/chat", json={}, headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "missing_query")

    def test_chat_valid_returns_envelope_when_ready(self) -> None:
        from phase_6_2.readiness import assess_readiness

        if not assess_readiness(load_config()).ready:
            self.skipTest("indexes or GenerationService not ready")
        resp = self.client.post(
            "/chat",
            json={"query": "expense ratio HSBC Gilt Fund Direct Growth"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertIn(data.get("outcome_type"), ("factual", "refusal", "abstention"))
        self.assertIn("assistant", data)
        self.assertTrue(data.get("display_text"))

    def test_chat_null_bytes_in_body(self) -> None:
        resp = self.client.post(
            "/chat",
            content=b'{"query":"hi\x00"}',
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 400)
        self.assertEqual(resp.json()["error"]["code"], "invalid_body")

    def test_chat_oversized_body(self) -> None:
        cfg = load_config()
        limits, _ = load_validation_limits(cfg)
        huge = json.dumps({"query": "x" * (limits.max_request_body_bytes + 100)})
        resp = self.client.post(
            "/chat",
            content=huge.encode(),
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 413)
        self.assertEqual(resp.json()["error"]["code"], "payload_too_large")


if __name__ == "__main__":
    unittest.main()
