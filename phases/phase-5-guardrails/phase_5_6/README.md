# Phase 5.6 — Generation service, evaluation, and Phase 6 handoff

End-to-end `answer(query)` pipeline: **Phase 4.6 retrieve → 5.2 → (5.3 | 5.4 | abstain) → 5.5**.

## Run

From `phases/phase-5-guardrails`:

```bash
python -m phase_5_6.run_service --query "expense ratio HSBC Gilt Fund Direct Growth"
python -m phase_5_6.run_service --eval-full
```

## Public API

```python
from phase_5_6.service import answer, GenerationService
from phase_5_6.contracts import GenerationRequest

envelope = answer("exit load HSBC Midcap Fund")
# or
envelope = GenerationService().answer(GenerationRequest(query="...", session_id=""))
```

## Outputs

| File | Description |
|------|-------------|
| `artifacts/eval/phase5_6_full_evaluation_report.json` | Red-team + factual generation eval |
| `artifacts/service/phase6_generation_handoff.json` | Phase 6 API/middleware handoff |

## Evaluation metrics

- Compliance pass rate
- Red-team pass rate
- Factual format pass rate
- Allowlist violation count (target: **0**)

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_5_6.py" -v
```
