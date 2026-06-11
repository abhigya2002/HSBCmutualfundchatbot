"""Tests for Phase 2.1 (workspace, config, registry bridge, dry enumeration)."""

from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from common.config import load_config, phase2_ingestion_root
from common.paths import ArtifactPaths
from common.registry_bridge import validate_registry_or_raise


class TestPhase21(unittest.TestCase):
    def test_default_config_loads(self):
        cfg = load_config()
        self.assertIn("artifact_root", cfg)
        self.assertIn("http", cfg)
        self.assertEqual(cfg["http"]["max_retries"], 3)

    def test_artifact_paths_relative(self):
        root = phase2_ingestion_root()
        cfg = load_config()
        paths = ArtifactPaths.from_config(cfg, root)
        self.assertTrue(str(paths.raw).endswith("raw") or paths.raw.name == "raw")
        self.assertEqual(paths.raw.parent, paths.root)

    def test_ensure_dirs(self):
        with tempfile.TemporaryDirectory() as tmp:
            t = Path(tmp)
            cfg = {
                "artifact_root": str(t / "art"),
                "directories": {"raw": "r", "clean": "c", "metadata": "m", "extracted": "e"},
            }
            paths = ArtifactPaths.from_config(cfg, Path(tmp))
            paths.ensure_dirs()
            self.assertTrue(paths.raw.is_dir())
            self.assertTrue(paths.clean.is_dir())
            self.assertTrue(paths.metadata.is_dir())
            self.assertTrue(paths.extracted.is_dir())
            self.assertTrue(paths.quarantine.is_dir())

    def test_validate_registry_or_raise(self):
        data = validate_registry_or_raise()
        self.assertEqual(len(data["entries"]), 16)

    def test_planned_paths_unique(self):
        root = phase2_ingestion_root()
        cfg = load_config()
        paths = ArtifactPaths.from_config(cfg, root)
        data = validate_registry_or_raise()
        seen: set[str] = set()
        for e in data["entries"]:
            p = str(paths.planned_raw_path(str(e["scheme"])))
            seen.add(p)
        self.assertEqual(len(seen), 16)


if __name__ == "__main__":
    unittest.main()
