# Phase 6.5 — Next.js Chat UI

Production-ready frontend matching the Stitch HSBC Mutual Fund Assistant design.

## Prerequisites

- Node.js 18+
- FastAPI backend running (`python -m phase_6_2.run_server` from `phase-6-api-ui`)

## Setup

```powershell
cd "d:\RAG Chatbot\phases\phase-6-api-ui\phase_6_5\frontend"
npm install
```

## Run

```powershell
# Terminal 1 — API
cd "d:\RAG Chatbot\phases\phase-6-api-ui"
python -m phase_6_2.run_server

# Terminal 2 — UI
cd "d:\RAG Chatbot\phases\phase-6-api-ui\phase_6_5\frontend"
npm run dev
```

Open [http://localhost:3000](http://localhost:3000)

## Environment

`.env.local`:

```
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
```

## Components

| Component | Purpose |
|-----------|---------|
| `Navbar.tsx` | Header, live status, verified badge |
| `WelcomeScreen.tsx` | Welcome + 3 sample questions (auto-submit) |
| `ChatBubble.tsx` | User/assistant bubbles, citation, copy |
| `TypingIndicator.tsx` | Loading dots |
| `InputBar.tsx` | Sticky input, disclaimer, debounce |
| `ErrorToast.tsx` | Network error toast |

## Security

- Citation URLs validated against 16-url allowlist (`src/lib/allowlist.ts`)
- External links use `rel="noopener noreferrer"`

## Design reference

Based on `stitch_hsbc_fund_assistant_ui` (index.html, DESIGN.md, screen.png).
