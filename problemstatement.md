# Project Specification: Mutual Fund FAQ Assistant (Facts-Only Q&A)

## Overview
The objective of this project is to build a facts-only FAQ assistant for mutual fund schemes, using Groww as the reference product context. The assistant will answer objective, verifiable queries related to mutual funds by retrieving information exclusively from official public sources (AMC websites, AMFI, and SEBI).

**Strict Constraint:** The system must avoid providing investment advice, opinions, or recommendations. Every response must include a single, clear source link.

## Core Architecture: RAG (Retrieval-Augmented Generation)
Implement a lightweight RAG pipeline to process a curated corpus of official documents and answer user queries based on that context.

---

## 1. Scope & Corpus Definition
### Asset Management Company (AMC) Selection
* **Selected AMC:** [Choose one, e.g., HDFC AMC, ICICI Prudential, or SBI Mutual Fund]
* **Schemes (3–5 diverse categories):**
    1.  Large-cap Fund
    2.  Flexi-cap Fund
    3.  ELSS (Tax Saving)
    4.  [Optional: Debt or Liquid Fund]

### Data Sources (15–25 URLs)
Collect official public URLs for the selected schemes, including:
* Scheme Factsheets
* Key Information Memorandum (KIM)
* Scheme Information Document (SID)
* AMC FAQ/help pages
* AMFI/SEBI guidance pages
* Statement and tax document download guides

---

## 2. Assistant Functional Requirements
### Factual Query Handling
The assistant must answer objective queries including:
* Expense ratio of a scheme
* Exit load details
* Minimum SIP amount
* ELSS lock-in period
* Riskometer classification
* Benchmark index
* Processes for downloading statements or capital gains reports

### Response Formatting Constraints
* **Length:** Maximum of 3 sentences.
* **Citation:** Exactly one citation link per response.
* **Footer:** Must include: `Last updated from sources: [Current Date/Source Date]`

---

## 3. Compliance & Refusal Logic
### Prohibited Content
* No investment advice or "Should I invest?" answers.
* No fund comparisons ("Which is better?").
* No performance calculations or return projections.
* **Note:** For performance queries, provide a link to the official factsheet only.

### Refusal Protocol
If a query is non-factual or advisory:
1.  Be polite and reinforce the "facts-only" limitation.
2.  Provide a relevant educational link (e.g., AMFI or SEBI resource).

### Privacy & Security (Strict)
**Do NOT collect, store, or process:**
* PAN or [Aadhaar Redacted] numbers
* Account numbers
* OTPs
* Personal Identifiable Information (Email/Phone)

---

## 4. User Interface (UI) Requirements
A simple, clean interface containing:
* **Welcome Message:** Introduction to the tool.
* **Example Questions:** Three clickable or visible sample prompts.
* **Visible Disclaimer:** `Facts-only. No investment advice.`

---

## 5. Technical Deliverables
### README.md
* Setup instructions.
* List of selected AMC and schemes.
* Architecture overview (RAG flow).
* Known limitations.

### Implementation Success Criteria
* Accurate retrieval from the curated corpus.
* Strict adherence to the 3-sentence limit.
* Consistent inclusion of valid source citations.
* Zero advisory or recommendation-based responses.
