# Phase 4 — Query understanding, retrieval, and re-ranking

**Architecture:** `phase-wise-architecture.md` (Phase 4).

## Goal

Classify queries, run hybrid retrieval **only** over chunks whose `source_url` is in the sixteen-URL allowlist, re-rank, and select a single citation URL per policy.

## Subphases

| Subphase | Folder | CLI | Status |
|----------|--------|-----|--------|
| 4.1 | `phase_4_1/` | `python -m phase_4_1.dry_load` | Implemented |
| 4.2 | `phase_4_2/` | `python -m phase_4_2.run_classify` | Implemented |
| 4.3 | `phase_4_3/` | `python -m phase_4_3.run_resolve` | Implemented |
| 4.4 | `phase_4_4/` | `python -m phase_4_4.run_retrieve` | Implemented |
| 4.5 | `phase_4_5/` | `python -m phase_4_5.run_rerank` | Implemented |
| 4.6 | `phase_4_6/` | `python -m phase_4_6.run_service` | Implemented |

Phase 3 handoff: `../phase-3-indexing/artifacts/phase4_retrieval_handoff.json`.

## Planned artifacts

| Artifact | Description |
|----------|-------------|
| Intent classifier | factual, performance-info, advisory/comparison, out-of-scope |
| Retrieval + re-rank service | Deterministic tie-breaks documented |
| Offline evaluation report | precision@k, citation relevance |

## Exit criteria (from architecture)

- Citations are always exactly one URL from the allowlist; scheme alignment meets agreed threshold on benchmark + adversarial set.
- Advisory/comparison/mixed-policy queries do not invoke hybrid retrieval.
- Consistent single-source selection with low hallucination risk; abstention path when evidence is weak.

Phase 4.6 validates these via `python -m phase_4_6.run_service --eval-full`.

## Edge cases

See [edge-cases/phase-4.md](../../edge-cases/phase-4.md).
