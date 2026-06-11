# Phase 5.3 — Refusal response composer

Produces policy-compliant refusal messages with exactly one allowlisted Groww link.

## Run

From `phases/phase-5-guardrails`:

```bash
python -m phase_5_3.run_compose --eval-benchmark
python -m phase_5_3.run_compose --refusal-type advisory
python -m phase_5_3.run_compose --query "Should I buy HSBC Gilt Fund?"
```

## Templates

Fixed copy in `templates/refusal.templates.json` for:

- `advisory`, `comparison`, `mixed_intent`, `out_of_scope`, `disambiguate`, `performance_info`

Phase 4 `message_hint` is internal guidance only — not echoed to users.

## Output contract

`RefusalAnswer`:

| Field | Description |
|-------|-------------|
| `body_text` | Fixed refusal message (no hyperlinks) |
| `citation_url` | Single allowlisted URL |
| `citation_markdown` | One markdown link |
| `disclaimer_line` | `Facts-only. No investment advice.` |

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_5_3.py" -v
```

## Outputs

| File | Description |
|------|-------------|
| `artifacts/eval/phase5_3_refusal_composer_report.json` | Benchmark from `--eval-benchmark` |
