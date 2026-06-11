# Phase 4.6 — Retrieval service, evaluation, and Phase 5 handoff

End-to-end pipeline composing **4.2 → 4.3 → 4.4 → 4.5** with refusal gating.

## Run

From `phases/phase-4-retrieval`:

```bash
python -m phase_4_6.run_service --query "expense ratio HSBC Gilt Fund"
python -m phase_4_6.run_service --eval-full
```

## API

```python
from phase_4_6.service import retrieve, RetrievalService
from phase_4_6.contracts import RetrievalRequest

outcome = retrieve("exit load HSBC Midcap Fund")
# outcome.outcome_type == "retrieval" | "refusal"
```

## Outputs

| File | Command |
|------|---------|
| `artifacts/eval/phase4_6_full_evaluation_report.json` | `--eval-full` |
| `artifacts/service/phase5_retrieval_handoff.json` | `--eval-full` (auto) |

## Evaluation

- **Factual benchmark:** citation accuracy, scheme-match rate (Phase 3 retrieval set)
- **Adversarial benchmark:** refusal cases skip hybrid; allowlist on all citations
- Thresholds in `config/retrieval.defaults.json` → `service`

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_4_6.py" -v
```
