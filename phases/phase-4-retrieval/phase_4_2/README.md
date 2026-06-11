# Phase 4.2 — Intent classification

Routes queries to **retrieve**, **refuse**, **performance_limited**, or **disambiguate** before hybrid search (Phase 4.4).

Aligned with [query-policy-matrix.md](../../phase-0-foundation/query-policy-matrix.md) (A1–A7, P1, R1–R5, O1).

## Run

From `phases/phase-4-retrieval`:

```bash
python -m phase_4_2.run_classify --query "expense ratio HSBC Gilt Fund"
python -m phase_4_2.run_classify --benchmark
```

## Intent labels → actions

| Intent | Action | Retrieval |
|--------|--------|-----------|
| `factual` | `retrieve` | Yes |
| `performance-info` | `performance_limited` | Limited path (Phase 5) |
| `advisory` | `refuse` | No |
| `comparison` | `refuse` | No |
| `out-of-scope` | `refuse` or `disambiguate` | No |
| `mixed` | `refuse` | No (refusal-first) |

## Configuration

- Rules: `config/intent.rules.json`
- Override: `INTENT_RULES_PATH`
- Optional LLM: set `feature_flags.llm_classifier` and `INTENT_LLM_ENABLED=1` (stub delegates to rules until wired)

## Outputs

| File | Command |
|------|---------|
| `artifacts/eval/phase4_2_intent_benchmark_report.json` | `--benchmark` |
| `artifacts/logs/intent.jsonl` | `--log-file artifacts/logs/intent.jsonl` |

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_4_2.py" -v
```
