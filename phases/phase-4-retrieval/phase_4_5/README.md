# Phase 4.5 — Re-ranking, thresholding, and citation selection

Deterministically picks one chunk and **one** allowlisted citation URL for Phase 5.

## Run

From `phases/phase-4-retrieval`:

```bash
python -m phase_4_5.run_rerank --query "expense ratio HSBC Gilt Fund"
python -m phase_4_5.run_rerank --benchmark
```

Pipeline: Phase 4.2 intent → 4.3 scheme → 4.4 hybrid → **4.5 re-rank + citation**.

## Scoring (documented weights)

| Signal | Config key | Default weight |
|--------|------------|----------------|
| Vector (normalized) | `channel_weights.vector` | 0.45 |
| Keyword (normalized) | `channel_weights.keyword` | 0.45 |
| Facet/intent match | `signal_weights.facet_match` | 0.25 |
| Lexical overlap | `signal_weights.lexical_overlap` | 0.15 |
| Scheme match boost | `signal_weights.scheme_match` | 0.15 |

## Tie-break (P4-12)

1. `final_score` descending  
2. `effective_date` descending (freshness)  
3. `chunk_id` ascending (deterministic)

## Citation policy (P4-06)

When scheme resolver is confident, `citation_url` follows the **resolver** URL; chunk text supplies evidence.

If no candidate passes `min_final_score` → `not_found_in_sources` with resolver or default URL.

## Configuration

- `config/rerank.defaults.json`
- Override: `RERANK_CONFIG_PATH`

## Tests

```bash
python -m unittest discover -s tests -p "test_phase_4_5.py" -v
```
