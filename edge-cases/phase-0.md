# Edge Cases — Phase 0: Foundation and Scope Freeze

Companion: `phase-wise-architecture.md` §Phase 0.

| ID | Edge case | Why it matters | Expected handling |
|----|-----------|----------------|-------------------|
| P0-01 | Stakeholder asks to add “just one” AMFI or AMC URL for credibility | Violates strict corpus allowlist | Document as **out of scope** for this phase; defer to future phase or reject scope change |
| P0-02 | Query taxonomy row is vague (e.g. “tell me about tax”) | Ambiguous allowed vs refusal | Classify as **refusal or narrow factual** in policy matrix with explicit examples |
| P0-03 | “Statement/tax process” overlaps with PII (user pastes PAN in sample question) | Privacy rule | Policy matrix: **no** collection; sample prompts must be PII-free; refusal wording defined |
| P0-04 | Two teams disagree on whether “minimum Lumpsum” is in scope | Inconsistent product | Freeze single definition; add to allowed intents or explicit refuse |
| P0-05 | Risk register empty or generic | Misses real risks | Capture: Groww HTML volatility, allowlist-only refusal links, robots/terms, model hallucination |
| P0-06 | Acceptance checklist omits “citation must be one of 16 URLs” | QA misses allowlist | Checklist must include: 3 sentences, one link, **link ∈ allowlist**, footer, facts-only |
| P0-07 | Scope document lists 17 schemes or wrong AMC | Registry drift | Single source of truth: architecture §2.1 table only |
| P0-08 | “Educational” refusal path assumed to use AMFI link | Conflicts architecture | Policy matrix states: **only** allowlisted Groww URLs if a link is required |
| P0-09 | Hindi/regional wording in scope (“ELSS क्या है”) | Multilingual not decided | Either **out of scope** for v1 or document “English only” |
| P0-10 | Success criteria still reference “official source” generically | Misaligned with Groww-only corpus | Reword to “grounded in allowlisted Groww pages” |

**Test hints:** Review meetings with red-lined policy matrix; sign-off checklist that explicitly checks allowlist and citation rules.
