# Phase 4.1 — Workspace, configuration, and Phase 3 index handoff

Validates retrieval workspace layout, loads Phase 3 handoff JSON, and dry-loads vector + BM25 indexes (no query classification).

## Run

From `phases/phase-4-retrieval`:

```bash
python -m phase_4_1.dry_load
```

Options:

- `--config PATH` — override `config/retrieval.defaults.json`
- `--json-out PATH` — write manifest (default: `artifacts/phase4_1_dry_manifest.json`)
- `--skip-index-load` — path/registry checks only (no Phase 3 imports)

## Outputs

| File | Description |
|------|-------------|
| `artifacts/phase4_1_dry_manifest.json` | Index version pins, counts, readiness for 4.2 |
| `artifacts/phase4_1_handoff_validation.json` | Same as manifest (validation snapshot) |

## Environment

| Variable | Purpose |
|----------|---------|
| `RETRIEVAL_CONFIG_PATH` | Config JSON path |
| `PHASE3_CHUNKING_ROOT` | Override chunking workspace |
| `PHASE3_INDEXING_ROOT` | Override indexing workspace |
| `PHASE4_RETRIEVAL_ARTIFACT_ROOT` | Override `artifacts/` root |

## Tests

```bash
cd phases/phase-4-retrieval
python -m unittest discover -s tests -p "test_phase_4_1.py" -v
```
