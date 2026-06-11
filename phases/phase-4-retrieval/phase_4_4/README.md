# Phase 4.4 — Hybrid retrieval (allowlist-scoped)

BM25 + vector search unioned by `chunk_id`, filtered to the 16 allowlisted Groww URLs.

## Run

From `phases/phase-4-retrieval`:

```bash
python -m phase_4_4.run_retrieve --query "expense ratio HSBC Gilt Fund"
python -m phase_4_4.run_retrieve --benchmark
```

Options:

- `--skip-intent` — skip Phase 4.2 refusal gate
- `--scheme SLUG` — force scheme filter
- `--k 5` — benchmark recall@k

## Pipeline integration

When run without `--skip-intent`:

1. Phase 4.2 intent gate (skips retrieval on refuse/disambiguate)
2. Phase 4.3 scheme resolution (applies `scheme=` filter when resolved)
3. Hybrid retrieval (this module)

## Configuration

- `config/hybrid.defaults.json` — `top_k_per_channel`, `fused_pool_size`, thresholds
- Override: `HYBRID_CONFIG_PATH`

## Outputs

| File | Command |
|------|---------|
| `artifacts/eval/phase4_4_hybrid_benchmark_report.json` | `--benchmark` |

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_4_4.py" -v
```
