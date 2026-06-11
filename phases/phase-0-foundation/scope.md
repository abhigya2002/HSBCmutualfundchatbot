# Scope document — Mutual Fund FAQ Assistant (facts-only)

**Version:** 1.0  
**Status:** Draft for stakeholder approval  
**Aligned with:** `phase-wise-architecture.md`, `problemstatement.md` (where compatible; corpus source is governed by architecture).

---

## 1. Product summary

Build a **facts-only** conversational FAQ assistant for **HSBC Mutual Fund** schemes. Answers must be objective and grounded in a **fixed corpus** of sixteen public scheme pages on **Groww**. The assistant does not provide investment advice, opinions, or recommendations.

**Reference product context:** Groww (for scheme page layout and user familiarity only). **Corpus:** only the URLs in section 3—not the full Groww site.

---

## 2. In-scope AMC and schemes

| # | Scheme name (Direct Growth) | Corpus URL |
|---|-----------------------------|------------|
| 1 | HSBC India Opportunities Fund | https://groww.in/mutual-funds/hsbc-india-opportunities-fund-direct-growth |
| 2 | HSBC Midcap Fund | https://groww.in/mutual-funds/hsbc-midcap-fund-direct-growth |
| 3 | HSBC Small Cap Fund | https://groww.in/mutual-funds/hsbc-small-cap-fund-direct-growth |
| 4 | HSBC Multi Cap Fund | https://groww.in/mutual-funds/hsbc-multi-cap-fund-direct-growth |
| 5 | HSBC Value Fund | https://groww.in/mutual-funds/hsbc-value-fund-direct-growth |
| 6 | HSBC Large and Mid Cap Fund | https://groww.in/mutual-funds/hsbc-large-and-mid-cap-fund-direct-growth |
| 7 | HSBC Equity Savings Fund | https://groww.in/mutual-funds/hsbc-equity-savings-fund-direct-growth |
| 8 | HSBC Infrastructure Fund | https://groww.in/mutual-funds/hsbc-infrastructure-fund-direct-growth |
| 9 | HSBC Multi Asset Allocation Fund | https://groww.in/mutual-funds/hsbc-multi-asset-allocation-fund-direct-growth |
| 10 | HSBC Focused Fund | https://groww.in/mutual-funds/hsbc-focused-fund-direct-growth |
| 11 | HSBC Gold ETF FoF | https://groww.in/mutual-funds/hsbc-gold-etf-fof-direct-growth |
| 12 | HSBC India Export Opportunities Fund | https://groww.in/mutual-funds/hsbc-india-export-opportunities-fund-direct-growth |
| 13 | HSBC Consumption Fund | https://groww.in/mutual-funds/hsbc-consumption-fund-direct-growth |
| 14 | HSBC Medium Duration Fund | https://groww.in/mutual-funds/hsbc-medium-duration-fund-direct-growth |
| 15 | HSBC Dynamic Bond Fund | https://groww.in/mutual-funds/hsbc-dynamic-bond-fund-direct-growth |
| 16 | HSBC Gilt Fund | https://groww.in/mutual-funds/hsbc-gilt-fund-direct-growth |

---

## 3. Corpus allowlist (strict)

For this project phase:

- **Exactly** the sixteen HTTPS URLs above constitute the entire corpus for ingest, index, retrieve, and cite.
- **No** additional URLs: no AMC microsites, AMFI, SEBI, PDF hosts, or pages reached only by following links off these URLs.
- **Every** user-visible citation hyperlink must be **one of** these sixteen URLs (canonical string; normalization rules in Phase 1).
- Ingestion is limited to the response body for each listed path; do not crawl the rest of Groww for corpus expansion.

Operational respect: comply with **robots.txt** and **Groww terms of use** when fetching these pages.

---

## 4. Functional scope (query types)

**In scope (factual, corpus-grounded):** objective attributes and processes **if** present on the allowlisted pages, including for example:

- Expense ratio (as stated on page)
- Exit load structure
- Minimum SIP / lumpsum where stated
- ELSS lock-in **only** for ELSS schemes in corpus (none in current sixteen unless page states tax-saving category; otherwise answer from page or clarify N/A)
- Riskometer / risk label as on page
- Benchmark name as on page
- Factual process hints shown on page (e.g. statements), without collecting user credentials

**Explicitly out of scope for v1:**

- Other AMCs or schemes not in the table
- Languages other than **English** (unless later phase adds policy)
- Personalized portfolio advice, suitability, or “should I invest”
- Fund-to-fund comparisons and rankings
- Return projections, performance marketing claims not grounded in cited page text

---

## 5. Response format (non-negotiable)

Every assistant reply must satisfy:

1. **Facts-only:** no advice, recommendations, or subjective ranking.
2. **Length:** at most **three** sentences (definition of “sentence” fixed in implementation tests; see Phase 5).
3. **Citation:** exactly **one** hyperlink, and its URL must be in the allowlist (section 3).
4. **Footer line:** `Last updated from sources: <date>` where `<date>` comes from agreed metadata (e.g. crawl timestamp or on-page “as of” if clearly present—see `query-policy-matrix.md`).

---

## 6. Privacy and security

Do **not** collect, store, or process:

- PAN, Aadhaar, account numbers, OTPs
- Email, phone, or other PII in logs or analytics

Sample UI prompts and documentation must be PII-free.

---

## 7. User interface (minimum)

- Welcome message introducing the tool.
- **Three** example factual questions (clickable or visible).
- Visible disclaimer: `Facts-only. No investment advice.`
- Citation link clearly shown per response.

---

## 8. Known limitation vs original problem statement

The original `problemstatement.md` refers to “official public sources (AMC, AMFI, SEBI).” **This project phase** follows `phase-wise-architecture.md`: corpus and citations are **restricted to the sixteen Groww scheme URLs** above. Educational links in refusal flows must also use one of these sixteen URLs (see `query-policy-matrix.md`).

---

## 9. Success criteria (reminder)

- Accurate retrieval from the curated allowlist corpus.
- Strict three-sentence cap and single allowlisted citation.
- Zero advisory or recommendation-style outputs.
- Compliance suite passes (to be implemented in later phases).
