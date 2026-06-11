# Phase 5.1 — Workspace, configuration, and Phase 4 handoff

Validates guardrails workspace, composer defaults, prohibited phrases, and `phase5_retrieval_handoff.json` from Phase 4.6.

## Run

From `phases/phase-5-guardrails`:

```bash
python -m phase_5_1.dry_load
```

## Configuration

| File | Purpose |
|------|---------|
| `config/guardrails.defaults.json` | Workspace, composer pins, handoff path |
| `config/prohibited.phrases.json` | Advisory/comparison/projection patterns for Phase 5.5 |

## Environment

| Variable | Purpose |
|----------|---------|
| `GUARDRAILS_CONFIG_PATH` | Override config JSON |
| `PHASE5_ARTIFACT_ROOT` | Override `artifacts/` root |
| `PHASE4_RETRIEVAL_ROOT` | Override Phase 4 retrieval workspace |

## Outputs

| File | Description |
|------|-------------|
| `artifacts/phase5_1_dry_manifest.json` | Readiness for Phase 5.2 |
| `artifacts/phase5_1_handoff_validation.json` | Validation snapshot |

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_5_1.py" -v
```
