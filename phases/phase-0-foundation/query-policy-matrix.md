# Query policy matrix

**Version:** 1.0  
**Companion:** [scope.md](scope.md), `phase-wise-architecture.md` §Phase 4–5.

This matrix defines how user intents are classified and what the system must do. **Redirect** here means “controlled response with mandatory allowlisted link,” not “send user to an external domain outside the sixteen URLs.”

---

## 1. Default citation for non-scheme-specific refusals

When a response must include a hyperlink but no single scheme clearly applies (e.g. generic advisory refusal, wrong AMC), use this **default allowlisted URL** unless product replaces it:

**Default:** `https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth` (HSBC Multi Cap Fund — Direct Growth)

Rationale: stable, diversified label; team may swap for another allowlisted row by updating this document only.

---

## 2. Intent classification matrix

| Intent code | User intent (examples) | Action | Citation rule | Notes |
|-------------|------------------------|--------|---------------|--------|
| **A1** | Expense ratio, TER, “how much is the fee” for named HSBC scheme | **Answer** (if in corpus) | Exactly **one** URL: that scheme’s Groww page from allowlist | Ground only in retrieved text |
| **A2** | Exit load, load structure | **Answer** | Same as A1 for resolved scheme | |
| **A3** | Minimum SIP, min investment, lumpsum minimum | **Answer** | Same | If not on page: say not stated + still one citation |
| **A4** | Lock-in, ELSS 3 year, tax saving lock | **Answer** / clarify | Same | If scheme not ELSS: state per page, no advice |
| **A5** | Riskometer, risk level | **Answer** | Same | |
| **A6** | Benchmark index name | **Answer** | Same | |
| **A7** | Statement / CAS / capital gains **process** (factual steps if on page) | **Answer** | Same | Do not ask for PAN; no account linking |
| **P1** | Past returns, “how much will I earn,” CAGR projection | **Refuse** advice/math projection; **limited factual** only if page shows past performance as data | Cite **that scheme’s** Groww URL | No invented numbers; no “you will get X%” |
| **R1** | Should I buy, is it good, recommend, suitability | **Refuse** | **Default** URL or most relevant scheme if user named one | Polite facts-only message |
| **R2** | Compare two funds, which is better, rank funds | **Refuse** | **Default** URL | No comparative metrics |
| **R3** | Non-HSBC scheme or AMC | **Refuse** / out of scope | **Default** URL | Explain corpus limit |
| **R4** | Mixed factual + advisory in one message | **Refuse-first** or factual-only with no advice (pick one policy; **recommended: refuse** the advisory part explicitly) | Per resolved scheme or **Default** | Document in tests |
| **R5** | Prompt injection (“ignore rules”, paste of system prompt) | **Refuse** / ignore instructions | **Default** URL | No new URLs |
| **O1** | Greeting, empty, off-topic (weather) | **Brief** non-financial reply or steer to factual MF questions | **Optional:** no link, or **Default** if product requires link every turn | Align with Phase 6 API contract |

---

## 3. “Allowed” query taxonomy (canonical list)

These are **candidates** for factual answering when the user’s scheme is in the sixteen and content exists on page:

- Expense ratio / TER  
- Exit load  
- Minimum SIP / minimum investment  
- Lock-in / ELSS-related facts **if applicable to scheme**  
- Riskometer  
- Benchmark  
- Download / statement / tax document process (factual only, from page)

---

## 4. Refusal taxonomy (canonical)

Always polite; reinforce facts-only; **no** investment recommendation.

- Advisory / suitability  
- Comparison between schemes or AMCs  
- Return **predictions** or personalized performance selling  
- Queries outside the sixteen-URL corpus  
- Requests that would require PII or account access  

**Educational / “learn more” link:** must be **one of the sixteen** Groww URLs (scheme-relevant preferred; else **Default** in §1).

---

## 5. Footer date policy (for acceptance tests)

| Situation | `Last updated from sources:` value |
|-----------|--------------------------------------|
| Preferred | ISO date of **last successful crawl** of the cited page (UTC), e.g. `2026-05-13` |
| If crawl date unavailable | Product must choose: omit assistant entirely, or use fixed copy “date unavailable” per risk acceptance (document in risk register) |

Phase 5 implementation must not invent a false “source date.”

---

## 6. Revision log

| Date | Change |
|------|--------|
| (fill) | Initial matrix |
