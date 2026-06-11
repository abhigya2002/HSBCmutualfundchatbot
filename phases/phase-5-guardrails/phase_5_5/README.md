# Phase 5.5 — Post-generation validators and repair

Hard-stops non-compliant refusal/factual drafts before Phase 6.

## Run

From `phases/phase-5-guardrails`:

```bash
python -m phase_5_5.run_validate --eval-benchmark
python -m phase_5_5.run_validate --query "expense ratio HSBC Gilt Fund Direct Growth"
python -m phase_5_5.run_validate --query "Should I buy HSBC Gilt?" --repair
```

## Validators

| Check | Edge case |
|-------|-----------|
| Sentence budget (≤3, semicolon clauses) | P5-04 |
| Exactly one allowlisted hyperlink | P5-01, P5-02, P5-07, P5-08 |
| Prohibited advisory/comparison/projection phrases | P5-03, P5-13 |
| Footer date policy for factual answers | P5-05 |
| Number grounding flags on factual drafts | P5-09 |

## Repair precedence

1. Strip extra body hyperlinks
2. Rebuild single allowlisted citation markdown
3. Truncate to sentence budget
4. Inject factual footer with approved unavailable date
5. Fallback to safe refusal template if still non-compliant

## Output contract

`ValidationResult`: `passed`, `violations[]`, `repaired`, `draft`, `display_text`

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_5_5.py" -v
```

## Outputs

| File | Description |
|------|-------------|
| `artifacts/eval/phase5_5_validation_report.json` | Benchmark from `--eval-benchmark` |
