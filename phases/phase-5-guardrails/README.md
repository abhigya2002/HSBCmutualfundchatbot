# Phase 5 — Guardrails, compliance engine, and response generation

**Architecture:** `phase-wise-architecture.md` (Phase 5).

## Goal

Enforce refusal rules, compose responses (≤3 sentences, one allowlisted link, footer), validate output, red-team prompts.

## Subphases

| Subphase | Folder | CLI | Status |
|----------|--------|-----|--------|
| 5.1 | `phase_5_1/` | `python -m phase_5_1.dry_load` | Implemented |
| 5.2 | `phase_5_2/` | `python -m phase_5_2.run_comply --eval-benchmark` | Implemented |
| 5.3 | `phase_5_3/` | `python -m phase_5_3.run_compose --eval-benchmark` | Implemented |
| 5.4 | `phase_5_4/` | `python -m phase_5_4.run_compose --eval-benchmark` | Implemented |
| 5.5 | `phase_5_5/` | `python -m phase_5_5.run_validate --eval-benchmark` | Implemented |
| 5.6 | `phase_5_6/` | `python -m phase_5_6.run_service --eval-full` | Implemented |

Phase 4 handoff: `../phase-4-retrieval/artifacts/service/phase5_retrieval_handoff.json`.

## Planned artifacts

| Artifact | Description |
|----------|-------------|
| Rule engine + middleware | Pre-generation policy enforcement |
| Response composer | Template aligned with `query-policy-matrix.md` |
| Validators | Sentence count, single hyperlink, host/path allowlist, prohibited phrases |
| Red-team suite | Jailbreak and advisory attempts |

## Exit criteria (from architecture)

- 100% pass on compliance test suite for refusal and formatting checks.

## Edge cases

See [edge-cases/phase-5.md](../../edge-cases/phase-5.md).
