# Phase 5.2 — Pre-generation compliance rule engine

Validates Phase 4 `RetrieveOutcome` before factual or refusal composition.

## Run

From `phases/phase-5-guardrails`:

```bash
python -m phase_5_2.run_comply --eval-benchmark
python -m phase_5_2.run_comply --query "Should I buy HSBC Gilt Fund?"
```

## Decisions

| Decision | Route | When |
|----------|-------|------|
| `refuse` | Phase 5.3 refusal composer | Phase 4 already refused or disambiguated |
| `abstain` | Abstention template | Empty evidence / `not_found_in_sources` |
| `allow_compose` | Phase 5.4 factual composer | Retrieved chunk present |

## Configuration

See `config/guardrails.defaults.json` → `compliance`:

- `abstain_on_not_found` — abstain when status is `not_found_in_sources` or chunk is empty
- `strip_query_injection` — strip injection patterns from query echo paths
- `require_chunk_text_for_compose` — block factual compose without chunk text

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_5_2.py" -v
```

## Outputs

| File | Description |
|------|-------------|
| `artifacts/eval/phase5_2_compliance_report.json` | Benchmark run from `--eval-benchmark` |
