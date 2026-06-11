# Edge Cases — Phase 2: Data Ingestion and Document Processing

Companion: `phase-wise-architecture.md` §Phase 2.

| ID | Edge case | Why it matters | Expected handling |
|----|-----------|----------------|-------------------|
| P2-01 | Fetcher receives redirect to login or captcha page | Poisoned “clean” text | Detect login/captcha markers; mark doc **failed**; do not index garbage |
| P2-02 | 301/302 to **different** path on groww.in | Off-allowlist content risk | If final URL not in allowlist → **fail** fetch for that seed |
| P2-03 | 429 rate limit or 503 | Incomplete corpus | Backoff + jitter; bounded retries; per-URL status in report |
| P2-04 | HTML is mostly JSON in `<script>` (SPA shell) | Empty visible text | Use documented render strategy (headless browser vs API if permitted); else fail with reason |
| P2-05 | Page locale differs (copy changes layout) | Parser breaks | Version parser per DOM signature; alert on hash change |
| P2-06 | Tables split across DOM for expense ratio / exit load | Lost structure | Prefer table-aware extraction; regression golden files per URL |
| P2-07 | User-generated or comment sections (if any) | Noise / liability | Strip non-main content per stable selectors; log stripped ratio |
| P2-08 | Relative links in HTML (`/mutual-funds/...`) | Accidental crawl expansion | **Do not** enqueue; ignore for ingestion scope |
| P2-09 | Inline `data:` or `blob:` resources | Irrelevant binary noise | Skip; do not treat as documents |
| P2-10 | gzip/brotli decode failure | Corrupt raw snapshot | Retry; checksum; quarantine raw bytes |
| P2-11 | Clock skew makes `last_fetched_at` inconsistent | Confusing audit trail | Use UTC; NTP note in runbook |
| P2-12 | Page A/B test shows different numbers to different IPs | Factual inconsistency | Store fetch metadata (region if any); single fetch policy per build |
| P2-13 | Very long single-line JSON in script | Token blowup in downstream chunker | Cap extracted text length per section with overflow flag |

**Test hints:** Fixture HTML for redirect, captcha, empty shell, and table-heavy snippet; assert no fetch for non-allowlisted final URL.
