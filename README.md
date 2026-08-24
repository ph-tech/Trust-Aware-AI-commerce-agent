# Trust-Aware AI Commerce Agent

A goal-driven AI commerce agent that helps customers find products via natural language while maintaining an Interaction Trust score that constrains upselling decisions. Revenue optimization is bounded by trust and respect for customer constraints.

## Core Principle
**LLM Interprets, Code Decides** — The LLM extracts structured intent from free text; all trust scoring, upsell decisions, and business logic are deterministic and auditable code.

## Architecture Overview

```
Customer message
    ↓
Intent extraction (heuristic) → category, budget, use-case
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
- **Frontend:** React (TypeScript) + Vite
- **Backend:** Python + FastAPI
- **Database:** SQLite (single-file, zero setup)
- **Testing:** pytest with isolated temp databases
- **CI:** GitHub Actions (pytest on push/PR)

## Build Timeline (14 days: Aug 22 - Sep 5)
- **Days 1-3:** Core pipeline end-to-end ✓
- **Days 4-7:** Intelligence & trust logic ✓
- **Days 8-10:** Stress testing & messy inputs ✓
- **Days 11-12:** UI polish & demo scenarios (in progress)
- **Days 13-14:** Buffer & final prep

## Demo Scenarios
1. Successful upsell with trust increase
2. Decline then re-engage (low trust, no pushiness)
3. Budget protection (agent respects stated limits)
4. Goal toggle (AOV vs Conversion mode differences)

## Key Files
- `backend/init_db.py` — Database initialization & product catalog seeding
- `backend/main.py` — FastAPI application with endpoints (/products, /intent, /score, /events, /roundtrip)
- `backend/trust.py` — Trust state management & audit logging
- `backend/scoring.py` — Deterministic scoring engine
- `frontend/src/App.tsx` — React chat UI with business goal selector
- `tests/test_roundtrip_integration.py` — End-to-end integration tests
- `tests/test_trust_events.py` — Trust scoring & audit log tests
- `tests/test_intent_stress.py` — Stress tests for messy inputs & concurrency

## Getting Started

### Prerequisites
- Python 3.8+
- Node.js 16+ (for frontend)
- pip & npm

### Backend Setup

1. Create and activate a Python virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Initialize the database:
   ```bash
   python backend/init_db.py
   ```
   This creates `data/catalog.db` and seeds it with products.

4. Start the backend server:
   ```bash
   uvicorn backend.main:app --reload
   ```
   Backend is now available at `http://127.0.0.1:8000`

### Frontend Setup

1. Install dependencies:
   ```bash
   cd frontend
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```
   Frontend is now available at `http://localhost:3000` and opens automatically.

### Test the Roundtrip

Once both backend and frontend are running, you can test the full flow:

**Via curl (backend only):**
```bash
curl -s -X POST http://127.0.0.1:8000/roundtrip \
  -H "Content-Type: application/json" \
  -d '{"text":"looking for a laptop under 1000","business_goal":"increase_aov"}'
```

**Via the UI:**
1. Open http://localhost:3000
2. Select a business goal (Increase AOV or Maximize Conversion)
3. Type a customer request (e.g., "I need a laptop under $1000")
4. Click Send and watch the agent respond

## Running Tests

Run all tests with pytest:
```bash
pytest tests/
```

Run specific test file:
```bash
pytest tests/test_roundtrip_integration.py -v
```

All tests use isolated temporary databases (see `temp_db` fixture in each test file).

## API Endpoints

- **POST `/roundtrip`** — Full roundtrip: intent → search → score → trust gate → response
  - Request: `{"text": "customer query", "business_goal": "increase_aov" | "maximize_conversion"}`
  - Response: `{"response": "agent message", "audit": {...}}`

- **POST `/products`** — Search products by query
- **POST `/intent`** — Extract intent from text
- **POST `/score`** — Score candidates against intent
- **POST `/events`** — Record audit events

## Development

### Backend Development
- Main app: `backend/main.py`
- Trust logic: `backend/trust.py`
- Database: `backend/init_db.py`
- Scoring: `backend/scoring.py`

### Frontend Development
- React app: `frontend/src/App.tsx`
- Styling: `frontend/src/App.css`
- Config: `frontend/vite.config.ts`

### CI/CD
- GitHub Actions workflow: `.github/workflows/pytest.yml`
- Runs pytest on every push and pull request
- Isolated databases ensure tests don't interfere with each other

## Notes

- Database path: `data/catalog.db` (created by `backend/init_db.py`)
- Frontend connects to backend at `http://127.0.0.1:8000`
- Tests create temporary databases in `/tmp` (or `%TEMP%` on Windows) and cleanup after
- Intent extraction uses heuristics (keywords, budget parsing) — ready for LLM integration via Anthropic API
- All upsell decisions and trust updates are deterministic and auditable

---

**Status:** Frontend, tests, and CI scaffolding complete. Backend core functionality ready. Demo scenarios in progress.
