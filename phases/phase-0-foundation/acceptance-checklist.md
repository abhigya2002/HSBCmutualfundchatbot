# Acceptance checklist — per assistant response

Use for **manual QA**, **UAT**, and **automated test design** (later phases). Check **every** item before marking a response as acceptable.

## Compliance and policy

- [ ] **Facts-only:** No investment advice, recommendation, suitability, or “you should / better to.”
- [ ] **No comparisons** between funds or AMCs (no “better,” “worse,” “prefer”).
- [ ] **No return projections** or guaranteed return language.
- [ ] **No PII** requested or echoed (PAN, Aadhaar, account, OTP, email, phone).

## Format (problem statement + architecture)

- [ ] **At most three sentences** (per project sentence-boundary rules).
- [ ] **Exactly one** user-visible hyperlink in the response body.
- [ ] That hyperlink’s URL is **identical** (after canonical normalization) to **one of** the sixteen Groww scheme URLs in [scope.md](scope.md) section 3.
- [ ] Footer line present: `Last updated from sources: <date>` and date policy matches [query-policy-matrix.md](query-policy-matrix.md) section 5.

## Grounding

- [ ] Factual claims in the answer are **supported** by retrieved content from the allowlisted corpus (no invented numbers or policies).
- [ ] If the corpus does not contain the fact: response **admits limitation** or refuses—no fabrication.

## Refusal paths

- [ ] Refusal messages remain polite and state the facts-only limitation.
- [ ] If a link is included in a refusal, it is still **only** an allowlisted URL (scheme-relevant or default per matrix).

## UI (when testing end-to-end)

- [ ] Disclaimer visible: `Facts-only. No investment advice.`
- [ ] Citation link is visible and clickable (or copyable in plain-text fallback).

## Sign-off

| Role | Name | Date | Pass/Fail |
|------|------|------|-----------|
| Reviewer | | | |
