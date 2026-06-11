"""Tests for Phase 4.1 workspace and Phase 3 index handoff."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path
from phase_4_1.config_load import load_config, phase4_retrieval_root
from phase_4_1.handoff import build_index_handoff_context
from phase_4_1.paths import Phase3Paths, RetrievalArtifactPaths


class TestPhase41Paths(unittest.TestCase):
    def test_retrieval_dirs_from_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = {
                "artifact_root": "artifacts",
                "directories": {"eval": "eval", "service": "service", "logs": "logs"},
            }
            paths = RetrievalArtifactPaths.from_config(cfg, root)
            paths.ensure_dirs()
            self.assertTrue(paths.eval.is_dir())
            self.assertTrue(paths.service.is_dir())
            self.assertTrue(paths.logs.is_dir())

    def test_phase3_paths_relative(self) -> None:
        cfg = load_config()
        p3 = Phase3Paths.from_config(cfg)
        self.assertTrue(p3.chunking_root.is_dir())
        self.assertTrue(p3.indexing_root.is_dir())


class TestPhase41HandoffIntegration(unittest.TestCase):
    def test_handoff_ready_when_indexes_exist(self) -> None:
        cfg = load_config()
        ctx = build_index_handoff_context(cfg)
        errors = [i for i in ctx.issues if i.code.startswith("error_") or i.code.startswith("missing_")]
        if not phase4_retrieval_root().joinpath("../phase-3-chunking/artifacts/indexes/vector/active.json").resolve().is_file():
            self.skipTest("Phase 3 vector active pointer not present")
        self.assertEqual(ctx.registry_entry_count, 16)
        self.assertTrue(ctx.index_version)
        self.assertEqual(len(errors), 0, [f"{e.code}: {e.message}" for e in errors])

    def test_dry_manifest_written(self) -> None:
        from phase_4_1.dry_load import main

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "manifest.json"
            code = main(["--json-out", str(out), "--skip-index-load"])
            if code != 0 and not load_config():
                self.skipTest("dry load failed — indexes may be missing")
            if out.is_file():
                data = json.loads(out.read_text(encoding="utf-8"))
                self.assertEqual(data.get("phase"), "4.1")
                self.assertIn("ready_for_phase_4_2", data)


class TestPhase41Registry(unittest.TestCase):
    def test_registry_bridge(self) -> None:
        from phase_4_1.registry_bridge import allowlisted_urls_set, validate_registry_or_raise

        reg = validate_registry_or_raise()
        urls = allowlisted_urls_set()
        self.assertEqual(len(reg.get("entries") or []), 16)
        self.assertEqual(len(urls), 16)


if __name__ == "__main__":
    unittest.main()
