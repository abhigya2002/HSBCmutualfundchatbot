# Phase 4.3 — Scheme resolution

Maps user queries to at most one of the **16** Phase 1 `scheme` slugs (or `ambiguous` / `unknown`).

## Run

From `phases/phase-4-retrieval`:

```bash
python -m phase_4_3.run_resolve --query "expense ratio HSBC Gilt Fund"
python -m phase_4_3.run_resolve --benchmark
```

## Resolution signals (priority)

1. Groww allowlisted URL in query  
2. Query-side aliases (`config/scheme.aliases.json`)  
3. Exact slug / display name / core phrase  
4. Conservative fuzzy match (typos → `ambiguous` if low confidence)

## Status values

| Status | Meaning |
|--------|---------|
| `resolved` | Single scheme + canonical `citation_url_candidate` |
| `ambiguous` | Two schemes, tie, or low confidence (P4-03, P4-05) |
| `unknown` | No HSBC scheme detected |

## Configuration

- `config/scheme.aliases.json` — nicknames + thresholds  
- Override: `SCHEME_ALIASES_PATH`

## Outputs

| File | Command |
|------|---------|
| `artifacts/eval/phase4_3_scheme_benchmark_report.json` | `--benchmark` |

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_4_3.py" -v
```
