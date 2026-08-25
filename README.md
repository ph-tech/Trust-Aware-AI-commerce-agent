# Trust-Aware AI Commerce Agent

A goal-driven AI commerce agent that helps customers find products via natural language while maintaining an Interaction Trust score that constrains upselling decisions. Revenue optimization is bounded by customer trust.

## Core Principle
**LLM Interprets, Code Decides** — The LLM extracts structured intent from free text; all trust scoring, upsell decisions, and business logic are deterministic and auditable code.

## Architecture Overview

```
Customer message
    ↓
Intent extraction (LLM) → category, budget, use-case
    ↓
Product search (catalog query)
    ↓
Candidate scoring (relevance, compatibility, margin)
    ↓
Rule evaluation (budget, prior declines, relevance)
    ↓
Trust state update (rules feed trust)
    ↓
Trust → Upsell Gate decision
    ↓
Audit log entry (JSON structured decision record)
    ↓
Response + cart update
```

## Tech Stack
- **Frontend:** React (TypeScript)
- **Backend:** Python + FastAPI
- **Database:** SQLite (single-file, zero setup)
- **Intent extraction:** Deterministic heuristic (ready to be replaced with an LLM)

## Build Timeline (14 days: Aug 22 - Sep 5)
- **Days 1-3:** Core pipeline end-to-end
- **Days 4-7:** Intelligence & trust logic
- **Days 8-10:** Stress testing & messy inputs
- **Days 11-12:** UI polish & demo scenarios
- **Days 13-14:** Buffer & final prep

## Demo Scenarios
1. Successful upsell with trust increase
2. Decline then re-engage (low trust, no pushiness)
3. Budget protection (agent respects stated limits)
4. Goal toggle (AOV vs Conversion mode differences)

## Key Files
- `backend/init_db.py` — SQLite schema and catalog seeding
- `backend/scoring.py` — Deterministic scoring engine (unit tested)
- `backend/main.py` — FastAPI application
- `backend/trust.py` — Trust state & rule evaluation
- `frontend/src/` — React chat UI, cart, decision panel

## Getting Started
1. Install backend dependencies: `pip install -r requirements.txt`
2. Initialize database: `python backend/init_db.py`
3. Start backend: `uvicorn backend.main:app --reload`
4. In another terminal, start the frontend: `cd frontend && npm install && npm run dev`

## Testing

Run the test suite with:

```bash
pytest -v
```

Each test creates and seeds its own temporary SQLite database, so it does not alter
the local `data/catalog.db` file.

---
**Status:** Scaffolding & foundation setup (Aug 22)
