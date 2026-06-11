# Edge Cases — Phase 7: Observability, QA, and Acceptance Testing

Companion: `phase-wise-architecture.md` §Phase 7.

| ID | Edge case | Why it matters | Expected handling |
|----|-----------|----------------|-------------------|
| P7-01 | Metric “retrieval hit” undefined | Gaming numbers | Define hit = chunk score ≥ threshold AND correct scheme |
| P7-02 | Flaky tests due to live Groww fetch | CI nondeterminism | Use recorded fixtures for unit/integration; live smoke separate |
| P7-03 | Manual QA checks “looks fine” without URL | Misses allowlist | Script: regex extract URLs; assert ⊆ 16 |
| P7-04 | Footer date compared to wall clock | False failure | Compare to `crawl_timestamp` or on-page date per spec |
| P7-05 | Refusal accuracy: human labels disagree | Metric noise | Adjudication guide + Cohen’s kappa on sample |
| P7-06 | Load test triggers Groww block | Legal/ops risk | Rate-limit internal tests; mock fetcher in load tests |
| P7-07 | Regression set includes outdated gold answer | Wrong pass | Version gold set with `corpus_version` |
| P7-08 | Edge case pack duplicates Phase 4-5 items | Wasted effort | Cross-reference IDs; ensure each automated once |
| P7-09 | Dashboard shows PII from error logs | Privacy breach | Log scrubber tests with synthetic PAN/email |
| P7-10 | “100% compliance suite” green but manual finds issue | False confidence | Weekly manual spot check + exploratory session |
| P7-11 | Mixed intent query scored as single label | Wrong path | Multi-label eval or worst-case policy (refusal-first) |
| P7-12 | Go-live checklist omits robots/terms compliance | Ops risk | Explicit legal/ToS tick for fetch cadence |

**Test hints:** CI job: compliance suite + link allowlist assertion on every PR; separate scheduled job for optional live URL health.
