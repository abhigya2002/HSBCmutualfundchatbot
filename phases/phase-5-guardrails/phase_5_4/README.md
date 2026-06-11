# Phase 5.4 — Factual response composer

Turns Phase 4 retrieval evidence into a ≤3-sentence factual draft with one citation and footer.

## Run

From `phases/phase-5-guardrails`:

```bash
python -m phase_5_4.run_compose --eval-benchmark
python -m phase_5_4.run_compose --query "expense ratio HSBC Gilt Fund Direct Growth"
```

## Composition policy

- **Mode:** extractive/template v1 by default; optional **Groq** rewording when `USE_GROQ=true` and `GROQ_API_KEY` are set in the project-root `.env`
- **Body:** 1–2 sentences grounded in `chunk_text`; optional clarifier for performance-limited queries (extractive path)
- **Groq:** model `llama-3.1-8b-instant`, temperature `0.1`, max tokens `200` — formats wording only; citation/footer still applied locally; Phase 5.5 validators unchanged
- **Citation:** exactly one allowlisted markdown link from Phase 4 `citation_url`
- **Footer:** `Last updated from sources: <date>` — uses `effective_date` or `date unavailable` (never invented)
- **Numbers:** uncited numerics are flagged and stripped when absent from the retrieved span

## Output contract

`FactualAnswer`: `body_text`, `citation_url`, `citation_markdown`, `footer_line`, `footer_date`, `evidence_chunk_id`

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_5_4.py" -v
```

## Outputs

| File | Description |
|------|-------------|
| `artifacts/eval/phase5_4_factual_composer_report.json` | Benchmark from `--eval-benchmark` |
