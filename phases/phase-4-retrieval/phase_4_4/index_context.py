"""Load hybrid indexes via Phase 4.1 handoff."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from phase_4_1.config_load import load_config
from phase_4_1.handoff import IndexHandoffContext, build_index_handoff_context
from phase_4_1.index_loader import LoadedIndexes, load_indexes
from phase_4_1.paths import Phase3Paths
from phase_4_4.embedder import create_embedder


@dataclass
class HybridIndexContext:
    handoff: IndexHandoffContext
    indexes: LoadedIndexes
    embedder: Any
    chunking_root: Any
    indexing_root: Any


def load_hybrid_context(config: dict | None = None) -> HybridIndexContext:
    cfg = config or load_config()
    handoff = build_index_handoff_context(cfg)
    if not handoff.ready:
        errors = [i.message for i in handoff.issues if i.code.startswith("error_") or i.code.startswith("missing_")]
        raise RuntimeError("Phase 3 index handoff not ready: " + "; ".join(errors[:3]))

    phase3 = Phase3Paths.from_config(cfg)
    loaded, load_issues = load_indexes(handoff, phase3.chunking_root, phase3.indexing_root)
    if loaded is None:
        raise RuntimeError("Failed to load indexes: " + "; ".join(i.message for i in load_issues))

    embedder = create_embedder(handoff)
    return HybridIndexContext(
        handoff=handoff,
        indexes=loaded,
        embedder=embedder,
        chunking_root=phase3.chunking_root,
        indexing_root=phase3.indexing_root,
    )
