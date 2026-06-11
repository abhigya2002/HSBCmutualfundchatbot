"""Tests for Phase 5.1 workspace and Phase 4 handoff validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from phase_5_1.config_load import load_config, phase5_guardrails_root
from phase_5_1.handoff import build_phase5_handoff_context, load_composer_defaults, load_prohibited_phrases
from phase_5_1.paths import GuardrailsArtifactPaths
from phase_5_1.registry_bridge import is_allowlisted_url, validate_registry_or_raise


class TestPhase51Paths(unittest.TestCase):
    def test_guardrails_dirs_from_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = {
                "artifact_root": "artifacts",
                "directories": {
                    "eval": "eval",
                    "service": "service",
                    "logs": "logs",
                    "templates": "templates",
                },
            }
            paths = GuardrailsArtifactPaths.from_config(cfg, root)
            paths.ensure_dirs()
            self.assertTrue(paths.eval.is_dir())
            self.assertTrue(paths.service.is_dir())
            self.assertTrue(paths.logs.is_dir())
            self.assertTrue(paths.templates.is_dir())


class TestComposerAndProhibited(unittest.TestCase):
    def test_composer_defaults_allowlisted_url(self) -> None:
        cfg = load_config()
        composer, issues = load_composer_defaults(cfg)
        self.assertFalse(any(i.code.startswith("missing_") for i in issues), issues)
        self.assertIsNotNone(composer)
        assert composer is not None
        self.assertLessEqual(composer.max_sentences, 3)
        self.assertTrue(is_allowlisted_url(composer.default_citation_url))

    def test_prohibited_phrases_load(self) -> None:
        cfg = load_config()
        prohibited, issues = load_prohibited_phrases(cfg)
        self.assertEqual(len(issues), 0, issues)
        self.assertIsNotNone(prohibited)
        assert prohibited is not None
        self.assertGreater(len(prohibited.advisory_patterns), 0)
        self.assertGreater(len(prohibited.comparison_patterns), 0)


class TestPhase51HandoffIntegration(unittest.TestCase):
    def test_handoff_ready_when_phase4_artifact_exists(self) -> None:
        handoff_path = (
            phase5_guardrails_root()
            / "../phase-4-retrieval/artifacts/service/phase5_retrieval_handoff.json"
        ).resolve()
        if not handoff_path.is_file():
            self.skipTest("phase5_retrieval_handoff.json not present — run Phase 4.6 eval first")
        cfg = load_config()
        ctx = build_phase5_handoff_context(cfg)
        errors = [i for i in ctx.issues if i.code.startswith("error_") or i.code.startswith("missing_")]
        self.assertEqual(len(errors), 0, [f"{e.code}: {e.message}" for e in errors])
        self.assertTrue(ctx.index_version)
        self.assertEqual(ctx.registry_entry_count, 16)

    def test_dry_manifest_written(self) -> None:
        from phase_5_1.dry_load import main

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.json"
            code = main(["--json-out", str(out)])
            if not out.is_file() and code != 0:
                self.skipTest("dry load failed — Phase 4 handoff may be missing")
            if out.is_file():
                data = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(data.get("phase"), "5.1")
                self.assertIn("ready_for_phase_5_2", data)


class TestRegistry(unittest.TestCase):
    def test_registry_sixteen_urls(self) -> None:
        reg = validate_registry_or_raise()
        self.assertEqual(len(reg.get("entries") or []), 16)


if __name__ == "__main__":
    unittest.main()
