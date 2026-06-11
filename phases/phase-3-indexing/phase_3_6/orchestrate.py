"""Orchestrate Phase 3.2 → 3.3 → 3.4 → 3.5 with shared index_version."""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Mapping


@dataclass
class PipelineStepResult:
    name: str
    exit_code: int
    command: str


@dataclass
class PipelineRunResult:
    index_version: str
    steps: list[PipelineStepResult] = field(default_factory=list)
    partial_corpus: bool = False
    schemes_expected: int = 16
    schemes_indexable: int | None = None

    @property
    def success(self) -> bool:
        return all(s.exit_code == 0 for s in self.steps)


def _run_module(cwd: Path, module: str, args: list[str] | None = None) -> PipelineStepResult:
    args = args or []
    cmd = [sys.executable, "-m", module, *args]
    proc = subprocess.run(cmd, cwd=str(cwd), capture_output=True, text=True)
    if proc.returncode != 0:
        sys.stderr.write(proc.stdout or "")
        sys.stderr.write(proc.stderr or "")
    return PipelineStepResult(
        name=module,
        exit_code=int(proc.returncode),
        command=" ".join(cmd),
    )


def _read_indexable_count(chunking_artifacts: Path) -> tuple[int, bool]:
    report = chunking_artifacts / "phase3_index_build_quality_report.json"
    if not report.is_file():
        return 0, True
    data = json.loads(report.read_text(encoding="utf-8"))
    per_scheme = data.get("per_scheme") or []
    indexable = sum(1 for r in per_scheme if r.get("indexable"))
    expected = 16
    partial = indexable < expected
    return indexable, partial


def run_full_index_pipeline(
    *,
    chunking_root: Path,
    indexing_root: Path,
    chunking_config_path: Path,
    index_version: str,
    skip_chunk: bool = False,
    skip_validate: bool = False,
    skip_embed: bool = False,
    skip_keyword: bool = False,
) -> PipelineRunResult:
    result = PipelineRunResult(index_version=index_version)

    if not skip_chunk:
        result.steps.append(
            _run_module(chunking_root, "phase_3_2.run_chunk", ["--config", str(chunking_config_path)]),
        )
    if not skip_validate:
        result.steps.append(
            _run_module(
                chunking_root,
                "phase_3_3.run_validate",
                ["--config", str(chunking_config_path), "--allow-warnings"],
            ),
        )
    if not skip_embed:
        result.steps.append(
            _run_module(
                chunking_root,
                "phase_3_4.run_embed",
                ["--config", str(chunking_config_path), "--index-version", index_version],
            ),
        )
    if not skip_keyword:
        indexing_config = indexing_root / "config" / "indexing.defaults.json"
        result.steps.append(
            _run_module(
                indexing_root,
                "phase_3_5.run_keyword_index",
                ["--config", str(indexing_config), "--index-version", index_version],
            ),
        )

    chunking_artifacts = chunking_root / "artifacts"
    indexable, partial = _read_indexable_count(chunking_artifacts)
    result.schemes_indexable = indexable
    result.partial_corpus = partial
    return result


def write_config_snapshot(
    indexing_artifacts: Path,
    index_version: str,
    chunking_config: Mapping[str, Any],
    indexing_config: Mapping[str, Any],
) -> Path:
    out = indexing_artifacts / "snapshots" / f"{index_version}_config.json"
    out.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "index_version": index_version,
        "captured_at_utc": datetime.now(timezone.utc).isoformat(),
        "chunking_config": dict(chunking_config),
        "indexing_config": dict(indexing_config),
    }
    out.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out
