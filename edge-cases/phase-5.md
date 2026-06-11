# Edge Cases — Phase 5: Guardrails, Compliance Engine, and Response Generation

Companion: `phase-wise-architecture.md` §Phase 5.

| ID | Edge case | Why it matters | Expected handling |
|----|-----------|----------------|-------------------|
| P5-01 | Model emits **two** markdown links | Violates single-citation rule | Post-validator **reject** → repair prompt or template-only citation injection |
| P5-02 | Model emits `groww.in` without `https://` | Link validator may pass/fail inconsistently | Normalize to full URL or fail validation |
| P5-03 | Model paraphrases advice without “should” | Bypass regex | Secondary classifier + “no recommendation” semantic check |
| P5-04 | Answer is 4 short clauses with semicolons | Sentence count ambiguity | Define sentence tokenizer rules (NLTK/spaCy/heuristic) in tests |
| P5-05 | Footer date missing from metadata | Architecture says hard-stop | Return safe refusal or “date unavailable” per product decision—**no** invented date |
| P5-06 | Citation URL is allowlisted but **wrong** scheme | User trust | Tie citation to retrieval `source_url` of top chunk (policy) |
| P5-07 | Refusal response includes non-allowlisted link in markdown footnote | Allowlist violation | Same validator as factual path |
| P5-08 | Unicode fullwidth colon / hidden chars in URL | Bypass string compare | Normalize Unicode; IDNA/punycode rules for host |
| P5-09 | Answer grounded but adds uncited number (“typically 1%”) | Hallucination | Strip numbers not in retrieved spans or reject |
| P5-10 | Jailbreak in system area of API | Policy bypass | Server-side system prompt fixed; user content delimited |
| P5-11 | Generator outputs footnote URL as plain text without hyperlink | UX / spec ambiguity | Policy: either require markdown link or accept one bare URL—**one** URL total |
| P5-12 | “Educational” refusal needs link; no scheme context | Which of 16? | Use team **default** Groww URL (document in Phase 0 matrix) |
| P5-13 | Prohibited phrase in **quoted** user question echo | False positive | Detect echoed quotes vs model-generated advice |

**Test hints:** Property tests on link count and host/path allowlist; red-team file from architecture deliverable.
