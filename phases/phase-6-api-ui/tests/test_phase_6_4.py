"""Tests for Phase 6.4 HTTP error and outcome contracts."""

from __future__ import annotations

import json
import unittest

from fastapi.testclient import TestClient

from phase_6_1.config_load import load_config
from phase_6_1.generation_bridge import ensure_phase5_on_path
from phase_6_2.app import create_app
from phase_6_2.readiness import assess_readiness
from phase_6_4.errors import assert_safe_error_payload, error_response
from phase_6_4.handoff_contract import load_handoff_contract, validate_envelope_against_handoff
from phase_6_4.http_policy import ERROR_STATUS_MAP, POLICY_OUTCOME_HTTP_STATUS
from phase_6_4.outcome_contract import REFUSAL_TYPES, ui_branch, validate_outcome_contract
from phase_6_4.responses import transport_error_response
from phase_6_4.run_contract_eval import run_eval

ensure_phase5_on_path(load_config())
from phase_5_1.registry_bridge import is_allowlisted_url


class TestApiErrorShape(unittest.TestCase):
    def test_error_response_shape(self) -> None:
        payload = error_response(code="invalid_json", message="Request body must be valid JSON")
        assert_safe_error_payload(payload)
        self.assertEqual(payload["error"]["code"], "invalid_json")

    def test_transport_error_no_leak(self) -> None:
        resp = transport_error_response(code="bad_gateway", message="Something went wrong.")
        self.assertEqual(resp.status_code, 502)
        body = json.loads(resp.body.decode())
        assert_safe_error_payload(body)
        self.assertNotIn("Traceback", body["error"]["message"])


class TestHttpPolicy(unittest.TestCase):
    def test_status_map(self) -> None:
        self.assertEqual(ERROR_STATUS_MAP["unsupported_media_type"], 415)
        self.assertEqual(ERROR_STATUS_MAP["payload_too_large"], 413)
        self.assertEqual(ERROR_STATUS_MAP["bad_gateway"], 502)
        self.assertEqual(POLICY_OUTCOME_HTTP_STATUS, 200)


class TestHandoffContract(unittest.TestCase):
    def test_handoff_loads(self) -> None:
        contract = load_handoff_contract()
        errors = [i for i in contract.issues if i.code.startswith("missing_")]
        self.assertEqual(len(errors), 0, contract.issues)
        self.assertIn("outcome_type", contract.envelope_fields)
        self.assertIn("refusal_type", contract.assistant_fields)
        self.assertEqual(contract.chat_path, "/chat")

    def test_contract_eval_passes(self) -> None:
        report = run_eval()
        self.assertTrue(report["passed"], report.get("checks"))


class TestOutcomeContract(unittest.TestCase):
    def test_refusal_branch(self) -> None:
        envelope = {
            "outcome_type": "refusal",
            "display_text": "No advice.",
            "assistant": {
                "answer_type": "refusal",
                "refusal_type": "advisory",
                "display_text": "No advice.",
                "body_text": "No advice.",
                "citation_url": "https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth",
            },
        }
        branch = ui_branch(envelope)
        self.assertEqual(branch["branch"], "refusal")
        self.assertEqual(branch["refusal_type"], "advisory")

    def test_refusal_types_set(self) -> None:
        self.assertIn("advisory", REFUSAL_TYPES)
        self.assertIn("comparison", REFUSAL_TYPES)


class TestChatHttpSemantics(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(create_app(load_config()))
        self.ready = assess_readiness(load_config()).ready

    def test_validation_error_is_not_200(self) -> None:
        resp = self.client.post("/chat", json={}, headers={"Content-Type": "application/json"})
        self.assertEqual(resp.status_code, 400)
        assert_safe_error_payload(resp.json())

    def test_refusal_is_http_200(self) -> None:
        if not self.ready:
            self.skipTest("service not ready")
        resp = self.client.post(
            "/chat",
            json={"query": "Should I buy HSBC Gilt Fund?"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data["outcome_type"], "refusal")
        self.assertIn(data["assistant"]["refusal_type"], REFUSAL_TYPES)
        issues = validate_outcome_contract(data)
        self.assertEqual(issues, [], issues)

    def test_factual_allowlisted_citation(self) -> None:
        if not self.ready:
            self.skipTest("service not ready")
        resp = self.client.post(
            "/chat",
            json={"query": "expense ratio HSBC Gilt Fund Direct Growth"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        contract = load_handoff_contract()
        env_issues = validate_envelope_against_handoff(data, contract)
        self.assertEqual(env_issues, [], [f"{i.code}: {i.message}" for i in env_issues])
        self.assertTrue(is_allowlisted_url(data["assistant"]["citation_url"]))

    def test_abstention_or_policy_outcome_not_http_error(self) -> None:
        if not self.ready:
            self.skipTest("service not ready")
        resp = self.client.post(
            "/chat",
            json={"query": "what is the expense ratio"},
            headers={"Content-Type": "application/json"},
        )
        self.assertEqual(resp.status_code, 200)
        self.assertIn(resp.json().get("outcome_type"), ("abstention", "factual", "refusal"))


if __name__ == "__main__":
    unittest.main()
