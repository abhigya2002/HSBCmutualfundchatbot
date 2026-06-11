"""Tests for Phase 3.1 workspace and Phase 2 handoff validation."""

from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from phase_3_1.handoff import validate_scheme_handoff
from phase_3_1.paths import Phase2ArtifactPaths, Phase3ArtifactPaths


class TestPhase31Paths(unittest.TestCase):
    def test_phase3_dirs_from_config(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            cfg = {
                "artifact_root": "artifacts",
                "directories": {
                    "chunks": "chunks",
                    "chunks_validated": "chunks_validated",
                    "embeddings": "embeddings",
                    "indexes": "indexes",
                    "logs": "logs",
                },
            }
            paths = Phase3ArtifactPaths.from_config(cfg, root)
            paths.ensure_dirs()
            self.assertTrue(paths.chunks.is_dir())
            self.assertTrue(paths.chunks_validated.is_dir())
            self.assertTrue(paths.embeddings.is_dir())
            self.assertTrue(paths.indexes.is_dir())
            self.assertTrue(paths.logs.is_dir())


class TestPhase31Handoff(unittest.TestCase):
    def _write_minimal_phase2(
        self,
        base: Path,
        scheme: str,
        *,
        extract_status: str = "ok",
        omit_md: bool = False,
    ) -> None:
        clean = base / "clean"
        meta = base / "metadata"
        clean.mkdir(parents=True)
        meta.mkdir(parents=True)
        md_path = clean / f"{scheme}.md"
        if not omit_md:
            md_path.write_text("# Fund\n\nExpense ratio 0.5%\n", encoding="utf-8")
        url = f"https://groww.in/mutual-funds/{scheme}"
        clean_doc = {
            "scheme": scheme,
            "source_url": url,
            "body_markdown_path": str(md_path),
            "sections": [{"level": 1, "title": "Fund", "start_char": 0, "end_char": 20}],
            "status_upstream": {
                "extract_status": extract_status,
                "normalize_status": "ok",
            },
        }
        (clean / f"{scheme}.clean.json").write_text(json.dumps(clean_doc), encoding="utf-8")
        doc_meta = {
            "scheme": scheme,
            "source_url": url,
            "extract_status": extract_status,
            "normalize_status": "ok",
        }
        (meta / f"{scheme}.json").write_text(json.dumps(doc_meta), encoding="utf-8")

    def test_indexable_when_artifacts_present(self) -> None:
        scheme = "hsbc-gilt-fund-direct-growth"
        url = f"https://groww.in/mutual-funds/{scheme}"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_minimal_phase2(base, scheme)
            phase2 = Phase2ArtifactPaths(root=base, clean=base / "clean", metadata=base / "metadata", quarantine=base / "q")
            cfg = {"handoff": {}}
            result = validate_scheme_handoff(scheme, url, phase2, cfg)
            self.assertTrue(result.indexable, result.blockers)
            self.assertEqual(result.extract_status, "ok")

    def test_blocked_on_empty_shell(self) -> None:
        scheme = "hsbc-gilt-fund-direct-growth"
        url = f"https://groww.in/mutual-funds/{scheme}"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_minimal_phase2(base, scheme, extract_status="empty_shell")
            phase2 = Phase2ArtifactPaths(root=base, clean=base / "clean", metadata=base / "metadata", quarantine=base / "q")
            result = validate_scheme_handoff(scheme, url, phase2, {})
            self.assertFalse(result.indexable)
            self.assertTrue(any("extract_status" in b for b in result.blockers))

    def test_blocked_on_missing_markdown(self) -> None:
        scheme = "hsbc-gilt-fund-direct-growth"
        url = f"https://groww.in/mutual-funds/{scheme}"
        with tempfile.TemporaryDirectory() as tmp:
            base = Path(tmp)
            self._write_minimal_phase2(base, scheme, omit_md=True)
            phase2 = Phase2ArtifactPaths(root=base, clean=base / "clean", metadata=base / "metadata", quarantine=base / "q")
            result = validate_scheme_handoff(scheme, url, phase2, {})
            self.assertFalse(result.indexable)
            self.assertIn("missing_clean_markdown", result.blockers)


if __name__ == "__main__":
    unittest.main()
