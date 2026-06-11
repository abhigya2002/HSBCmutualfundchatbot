# Edge Cases — Phase 6: API and UI Experience

Companion: `phase-wise-architecture.md` §Phase 6.

| ID | Edge case | Why it matters | Expected handling |
|----|-----------|----------------|-------------------|
| P6-01 | Extremely long user message (MB of text) | DoS / cost | Max body size; truncate with 413/400 |
| P6-02 | Null bytes / invalid UTF-8 in JSON | Parser errors | Reject with 400; log without storing raw payload |
| P6-03 | `Content-Type` wrong (`text/plain`) | Skips validation | Strict content-type; 415 |
| P6-04 | Missing disclaimer in UI theme (white on white) | Compliance visibility | Automated visual or DOM assert for disclaimer text |
| P6-05 | Sample question clicks send advisory wording | Bad UX / compliance | Sample prompts must be purely factual |
| P6-06 | Citation `target="_blank"` without `rel` | Security | `rel="noopener noreferrer"` on external link |
| P6-07 | XSS via assistant markdown in UI | Security | Sanitize markdown; allowlist link href to 16 URLs only in renderer |
| P6-08 | Double-submit / rapid clicks | Duplicate costly calls | Debounce; idempotency key optional |
| P6-09 | Offline / API 502 | User sees empty error | Friendly error; no leak of stack traces |
| P6-10 | Session “memory” stores prior PAN user pasted | PII violation | Stateless: no transcript persistence or immediate redaction |
| P6-11 | SSE/streaming partial JSON | Client renders half link | Buffer until message complete or stream-safe protocol |
| P6-12 | Mobile viewport hides footer “last updated” | Spec miss | Scroll-safe layout; assert footer in viewport on key breakpoints |
| P6-13 | Copy-paste from UI strips link | User loses citation | Plain-text fallback line with full URL |

**Test hints:** Contract tests for `/chat`; Cypress/Playwright for disclaimer + citation; fuzz JSON boundary sizes.
