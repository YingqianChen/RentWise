# RentWise

This README is the **canonical project document** for the active codebase.

If older notes or refactor docs disagree with this file, treat this README as the current source of truth. From this point on, project status, roadmap, and review notes should be updated here instead of being split across multiple new documents.

RentWise is being rebuilt from a Streamlit prototype into a monorepo with:

- `backend/`: FastAPI + SQLAlchemy + LangGraph
- `frontend/`: Next.js + React + TypeScript
- `legacy/`: archived Streamlit prototype code for reference only

## Current Product Scope

The rebuilt app now covers Phase 1 stabilization plus an initial Phase 2 compare workflow.

### Candidate-pool workflow

The active product focuses on a candidate-pool decision workflow:

- user registration and login
- search project creation
- search project deletion
- text-only candidate import
- automatic extraction and assessment after import
- dashboard summary with action-oriented priority candidates and investigation items
- dashboard investigation checklist now groups shared blockers instead of repeating the same prompt for each listing
- candidate detail view with reassess / shortlist / reject actions
- candidate editing with automatic reassessment
- candidate detail now prioritizes decision blockers and next questions before deeper structured details
- top-level first-pass recommendation:
  - shortlist recommendation
  - not ready
  - likely reject

### Compare workflow

The current compare experience is designed as a shortlist decision workspace rather than a field table:

- manual candidate selection from the dashboard
- compare workspace for 2 or more selected candidates
- decision grouping instead of fake exact ranking:
  - best current option
  - viable alternatives
  - not ready for fair comparison
  - likely drop
- explanation-rich compare cards with:
  - why the candidate is in its group
  - main tradeoff
  - open blocker
  - next action
- recommended next actions for the compare set:
  - who to contact first
  - what to ask next
  - who is ready for viewing
  - who can be deprioritized
- suggested compare preview on the dashboard
- compare context on the candidate detail page so the decision story stays consistent across surfaces
- LLM-assisted agent briefing on the compare page, focused on:
  - current take
  - why now
  - what could change
  - today's move
  - confidence note
- compare page now keeps supporting differences shorter so the main decision flow stays on briefing, groups, and next actions

Not in the current scope:

- image upload / OCR
- RAG-driven district workflow
- commute calculation
- saved compare history
- map-backed commute support

## What The Product Is Trying To Be

RentWise is not meant to be a field extractor or a generic chat assistant.

The current product direction is:

- a candidate-pool decision workspace
- a compare-driven shortlist tool
- an agent-assisted explanation layer

The intended user value is:

- help users decide which listings deserve attention
- make uncertainty visible instead of hiding it
- explain tradeoffs in plain language
- turn "I have several options and do not know what to do next" into an actionable workflow

## Repository Layout

```text
RentWise/
  backend/
  frontend/
  legacy/
  docs/
```

## Backend Setup

```bash
cd backend
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

If your local PostgreSQL database was created by the earlier startup `create_all()` flow, run this one-time command instead before switching to Alembic-managed migrations:

```bash
alembic stamp head
```

Then continue to use:

```bash
alembic upgrade head
```

`stamp head` only aligns Alembic's recorded revision. It does not add missing tables or columns.

Backend API:

- `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`

## Frontend Setup

```bash
cd frontend
npm install
copy .env.local.example .env.local
npm run dev
```

Frontend:

- `http://localhost:3000`

## Environment Variables

### Backend

Required:

- `SECRET_KEY`
- `DATABASE_URL`
- `LLM_PROVIDER`

Optional provider settings:

- `GROQ_API_KEY`
- `GROQ_MODEL`
- `OLLAMA_HOST`
- `OLLAMA_API_KEY`
- `OLLAMA_MODEL`

Note:

- The rebuilt backend currently targets PostgreSQL.
- SQLite is not a supported runtime for the current schema.

### Frontend

- `NEXT_PUBLIC_API_URL`

Default:

- `http://localhost:8000`

## Product Notes

- `legacy/streamlit_app/` is not the active product entry point.
- Database schema is now managed with Alembic.
- Run `alembic upgrade head` before starting the backend on a fresh environment.
- If you already had tables from the older startup-created schema, run `alembic stamp head` once to align Alembic with the existing database, then keep using `alembic upgrade head` for every later schema change.
- If you see errors like `column candidate_extracted_info.suspected_sdu does not exist`, your code is ahead of your local database schema. Run `alembic upgrade head` in `backend/`.
- Project deletion removes related candidates, assessments, and investigation items through database cascade rules.
- Candidate editing is currently available from the candidate detail page.
- Compare results are generated on demand and are not persisted yet.
- Dashboard can surface a suggested compare set based on the current shortlist shape.
- Candidate detail can open a compare workspace centered on the current candidate.
- Compare page now includes an LLM-assisted briefing layer with deterministic fallback if the model call fails.
- Candidate detail now pushes structured fields and source text into supporting sections so the decision read comes first.
- Dashboard now treats open questions as a grouped investigation checklist rather than a repeated per-listing warning feed.
- Frontend API error handling now keeps real backend response errors separate from true network failures, so candidate edit/save surfaces more actionable messages.
- Repair responsibility assessment now uses an LLM-normalized repair note plus conservative rule-based semantics, so signals like agency-supported repairs are treated as positive but still unconfirmed instead of being collapsed into a generic unknown.
- Lease term and move-in timing now follow the same pattern: the LLM first normalizes the clause text, then conservative semantic rules decide whether the signal looks standard, rigid, unstable, fit, uncertain, or mismatched.
- Candidate detail now translates internal clause states into user-facing explanations instead of exposing raw labels like `rigid` or `uncertain` directly.
- Local environment files such as `backend/.env` and `frontend/.env.local`, along with local caches and build artifacts, must stay out of git to avoid leaking secrets or machine-specific state.

## UX Reality Check

One of the biggest current product risks is information overload.

The codebase can already generate:

- structured extraction
- cost assessment
- clause assessment
- candidate assessment
- compare grouping
- compare explanation
- next-step guidance

That is useful, but it also creates a risk:

- too much structured output
- too many repeated explanations
- too many page sections competing for attention

The current direction is therefore:

- keep the decision path visible
- push supporting detail lower on the page
- reduce duplicate explanation across sections
- use explanation to support decisions, not to bury them

## Phase Status

### Phase 1

Phase 1 is effectively complete:

- auth
- projects
- candidate import and reassessment
- dashboard
- candidate detail
- project deletion
- candidate editing
- Alembic migrations
- test coverage for the main backend flows

### Phase 2

Phase 2 compare MVP is active:

- manual compare-set selection
- grouped shortlist comparison
- compare explanation and tradeoff output
- compare context from dashboard and candidate detail
- LLM-assisted compare briefing

### Phase 2.5

Phase 2.5 is partially active:

- compare page already has an agent-style briefing layer
- the next likely work in this area is stronger guidance and evidence-backed explanation

## Evidence, Benchmark, and Commute Roadmap

The next evidence-related work should not be treated as one generic "RAG" project.

It should be split into three tracks.

### 1. Benchmark Layer

Source:

- `document/SDU_median_rents.pdf`

Current finding:

- this PDF yields extractable text
- but it is specifically about subdivided units
- and the document itself says it is for general reference only

What this means:

- this should **not** be treated as a universal market-rent truth source
- it should become a **structured benchmark layer**, not generic vector RAG
- it is suitable only as a narrow SDU benchmark, not as a general district rent benchmark for all listings

Recommended use:

- candidate detail cost context
- compare support note
- light dashboard benchmark hint

Recommended order:

1. extract district-level benchmark data
2. store it as structured data
3. build a `BenchmarkService`
4. detect whether a candidate is likely an SDU using rules first and LLM support second
5. use it only when the candidate type and context make the benchmark meaningful

Current implementation status:

- benchmark evidence MVP is active on candidate detail and compare
- benchmark data is currently served from a versioned local structured data file, not a database table yet
- likely SDU now uses rules plus extraction support

Recommended benchmark rules:

- first version matching can stay at the district level
- benchmark should only be shown when the candidate has a district
- benchmark should only be shown when the candidate is likely an SDU
- benchmark should keep an explicit disclaimer:
  - for subdivided units only
  - general reference only
  - not property-specific

What not to do:

- do not use RAG for this benchmark lookup path
- do not show this benchmark for every listing by default
- do not feed benchmark data directly into the main assessment or hidden compare score

### 2. Tenancy Evidence Layer

Source:

- `document/AGuideToTenancy_ch.pdf`

Current finding:

- simple PDF extraction returns no usable text
- this strongly suggests the PDF is scan-heavy or image-based

What this means:

- this source is **not ready for text RAG yet**
- OCR is a prerequisite
- even after OCR, this should be treated as a narrow explanation-support retrieval layer, not as a main scoring engine

Recommended use after OCR:

- candidate detail clause explanation
- compare briefing evidence note
- future agent guidance support

Recommended order:

1. add OCR
2. inspect OCR quality manually
3. chunk only after the text is acceptable
4. add narrow retrieval for explanation support

Likely value of RAG here:

- explain why a clause or tenancy issue matters
- support a candidate detail evidence note
- support compare briefing rationale

What RAG is unlikely to do well here:

- replace structured extraction
- provide stable legal conclusions
- act as a universal answer engine for every housing question

### 3. Commute Support Layer

Current direction:

- single-destination commute support is the approved first shape
- commute remains support evidence, not a hidden scoring engine

Project-level model needed:

- commute enabled flag
- destination label
- destination query
- commute mode
- max commute minutes

Candidate-level model needed:

- address text
- building name
- nearest station
- location confidence
- location source

Recommended interaction:

- project commute setup is optional, not required at creation time
- candidate location should be extraction-first with user correction when needed
- candidate detail and compare can show commute evidence only when destination and location inputs are strong enough

Recommended order:

1. add project-level commute configuration
2. add candidate-level location evidence
3. update extraction to draft location evidence
4. let users correct location evidence in candidate editing
5. add a narrow map-backed `CommuteService`
6. surface commute evidence in candidate detail and compare

What not to do:

- do not treat district-only data as sufficient for commute estimation
- do not connect map capability before the location model exists
- do not add commute minutes into the main compare score in the first version

## Current Recommendation For The Team

If the team wants to improve the product without bloating it, the best order is:

1. keep reducing information duplication in the current UI
2. add the SDU benchmark layer from the median-rent PDF as structured benchmark data
3. decide whether OCR for the tenancy guide is worth the dependency cost, then only add narrow retrieval if the OCR quality is acceptable
4. add commute only after the project and candidate location models are in place

This is the most honest order.

It keeps the decision workflow stable while adding evidence where it is actually useful.

## Testing

Fast local suite:

```bash
cd backend
python -m unittest discover -s tests -p "test_*.py"
```

Real PostgreSQL-backed integration flow:

```bash
cd backend
set RUN_DB_INTEGRATION=1
.\venv\Scripts\python.exe -m unittest tests.integration.test_db_flow
```

The DB-backed test covers:

- register
- create project
- import candidate
- fetch dashboard

The current test suite also covers:

- action-oriented priority ranking
- investigation checklist generation
- top-level candidate recommendation
- compare grouping and compare explanation output
- compare route response shape
- compare briefing fallback behavior
- grouped investigation checklist behavior

## Team Review Notes

Two current product truths are worth keeping in mind during review:

1. More analysis output does not automatically produce better decisions.
   - The product is strongest when the user can tell what to do next within a few seconds.

2. External evidence should support trust, not create fake precision.
   - benchmark data should stay scoped
   - tenancy guide support should wait for OCR
   - commute should wait for a real location model
