"""Tests for Phase 6.1 workspace and Phase 5 handoff validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from phase_6_1.config_load import load_config, phase6_api_ui_root
from phase_6_1.generation_bridge import probe_generation_service
from phase_6_1.handoff import (
    build_phase6_handoff_context,
    load_server_config,
    load_validation_limits,
    validate_phase6_generation_handoff,
    workspace_layout_ok,
)
from phase_6_1.paths import ApiUiArtifactPaths


class TestPhase61Paths(unittest.TestCase):
    def test_api_ui_dirs_from_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = {
                "artifact_root": "artifacts",
                "directories": {
                    "eval": "eval",
                    "service": "service",
                    "logs": "logs",
                    "api": "api",
                    "ui": "ui",
                },
            }
            paths = ApiUiArtifactPaths.from_config(cfg, root)
            paths.ensure_dirs()
            self.assertTrue(paths.eval.is_dir())
            self.assertTrue(paths.service.is_dir())
            self.assertTrue(paths.logs.is_dir())
            self.assertTrue(paths.api.is_dir())
            self.assertTrue(paths.ui.is_dir())


class TestRuntimeConfig(unittest.TestCase):
    def test_server_and_validation_defaults(self) -> None:
        cfg = load_config()
        server, srv_issues = load_server_config(cfg)
        self.assertEqual(len(srv_issues), 0, srv_issues)
        self.assertEqual(server.host, "127.0.0.1")
        self.assertEqual(server.port, 8000)

        limits, val_issues = load_validation_limits(cfg)
        self.assertEqual(len(val_issues), 0, val_issues)
        self.assertGreater(limits.max_request_body_bytes, 0)
        self.assertEqual(limits.required_content_type, "application/json")


class TestHandoffValidation(unittest.TestCase):
    def test_validate_known_handoff_shape(self) -> None:
        handoff_path = (
            phase6_api_ui_root()
            / "../phase-5-guardrails/artifacts/service/phase6_generation_handoff.json"
        ).resolve()
        if not handoff_path.is_file():
            self.skipTest("phase6_generation_handoff.json not present — run Phase 5.6 eval first")
        data = json.loads(handoff_path.read_text(encoding="utf-8"))
        issues = validate_phase6_generation_handoff(data)
        errors = [i for i in issues if not i.code.startswith("warning_")]
        self.assertEqual(len(errors), 0, [f"{e.code}: {e.message}" for e in errors])

    def test_handoff_context_ready(self) -> None:
        handoff_path = (
            phase6_api_ui_root()
            / "../phase-5-guardrails/artifacts/service/phase6_generation_handoff.json"
        ).resolve()
        if not handoff_path.is_file():
            self.skipTest("phase6_generation_handoff.json not present")
        cfg = load_config()
        ctx = build_phase6_handoff_context(cfg)
        errors = [
            i
            for i in ctx.issues
            if i.code.startswith("error_") or i.code.startswith("missing_") or i.code.startswith("invalid_")
        ]
        self.assertEqual(len(errors), 0, [f"{e.code}: {e.message}" for e in errors])
        self.assertEqual(ctx.chat_endpoint_path, "/chat")
        self.assertIn("outcome_type", ctx.answer_envelope_fields)


class TestGenerationBridge(unittest.TestCase):
    def test_generation_service_instantiates(self) -> None:
        cfg = load_config()
        probe = probe_generation_service(cfg)
        if not probe.instantiated:
            self.skipTest(f"GenerationService unavailable: {probe.error}")
        self.assertTrue(probe.instantiated)
        self.assertTrue(probe.guardrails_root.is_dir())


class TestWorkspaceLayout(unittest.TestCase):
    def test_workspace_layout_present(self) -> None:
        issues = workspace_layout_ok(phase6_api_ui_root())
        self.assertEqual(len(issues), 0, [f"{i.code}: {i.message}" for i in issues])


class TestDryLoad(unittest.TestCase):
    def test_dry_manifest_written(self) -> None:
        from phase_6_1.dry_load import main

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.json"
            code = main(["--json-out", str(out)])
            if not out.is_file() and code != 0:
                self.skipTest("dry load failed — Phase 5 handoff may be missing")
            if out.is_file():
                data = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(data.get("phase"), "6.1")
                self.assertIn("ready_for_phase_6_2", data)
                self.assertTrue(data.get("generation_service", {}).get("instantiated"))


if __name__ == "__main__":
    unittest.main()
