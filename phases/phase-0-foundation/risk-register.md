# Risk register — initial

**Version:** 1.0  
**Review cadence:** After Phase 2 ingestion and before go-live (Phase 8).

| ID | Risk | Likelihood | Impact | Mitigation | Owner | Status |
|----|------|------------|--------|------------|-------|--------|
| R-01 | Groww HTML structure changes; parser returns empty or wrong text | Med | High | Versioned parsers, golden tests, alerts on parse success drop | TBD | Open |
| R-02 | Model hallucinates numbers or policies not on page | Med | High | Strict RAG grounding, validator, low-temperature or constrained decoding | TBD | Open |
| R-03 | User receives advisory content despite policy | Low | Critical | Refusal-first rules, regex + classifier, post-hoc link/sentence validators | TBD | Open |
| R-04 | Citation URL is allowlisted but wrong scheme | Med | Med | Tie citation to retrieved `source_url` / resolved entity; tests | TBD | Open |
| R-05 | Strict allowlist conflicts with “educational AMFI/SEBI link” in original spec | Low | Med | Documented in scope; use allowlisted Groww default only | TBD | Accepted |
| R-06 | Rate limiting or blocking from Groww during refresh | Med | Med | Backoff, respectful cadence, legal review of ToS/robots | TBD | Open |
| R-07 | PII accidentally logged from user paste | Med | High | No raw body logging in prod; scrubbers; stateless design | TBD | Open |
| R-08 | Footer date wrong or invented | Low | Med | Policy: crawl timestamp only; hard-stop if missing per matrix | TBD | Open |
| R-09 | Single corpus tier: facts on Groww may lag AMC filings | Med | Med | Disclosure in README; refresh SLO in Phase 8 | TBD | Open |
| R-10 | Non-English queries produce garbage or unsafe output | Med | Low | Phase 0 scope: English only v1; detect and refuse politely | TBD | Open |

## Change log

| Date | Change |
|------|--------|
| (fill) | Initial risks |
