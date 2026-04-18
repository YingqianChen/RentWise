# RentWise

RentWise is a Hong Kong rental research workspace. It helps a renter organize
rental candidates, compare them, and decide what to verify next — instead of
guessing from noisy listings.

This repository is the **MSc coursework submission** version. Active development
continues on a separate fork; this tree is frozen at the submission state.

**Language**: [English](README.md) • [中文](README_zh.md)

---

## What RentWise does

- **Candidate pool** — Paste or upload a rental listing (text, image, screenshot,
  PDF). The system extracts structured fields (address, rent, area, layout,
  utilities, fees), stores the raw source, and tags which fields are missing.
- **Per-candidate assessment** — For each candidate the system runs a set of
  evidence checks: SDU rent benchmark (is this price reasonable for the
  district/size?), cost breakdown (rent + management fee + rates + est. bills),
  clause-level flags (deposit, early termination, agency fee, repairs), and a
  priority score.
- **Compare view** — Side-by-side table and short written briefing for any 2–5
  candidates, so the user can see where they trade off.
- **Investigation items** — The system produces a short list of open questions
  per candidate ("confirm agency fee split", "ask about internet cost",
  "verify landlord identity"), so the next message to the landlord/agent
  writes itself.

The product philosophy is honest-assistant: don't rank for the user, surface
evidence and missing info so the user ranks with confidence.

---

## Repository layout

```
backend/       FastAPI + SQLAlchemy async + Alembic
  app/
    api/v1/          auth, projects, candidates, comparison, dashboard, investigation
    services/        domain logic (benchmark, extraction, assessment, ...)
    integrations/    LLM provider + prompts
    agent/           LangGraph investigation agent (experimental)
    db/              SQLAlchemy models
    schemas/         Pydantic request/response models
    data/            SDU rent benchmark JSON
  alembic/           migrations
  tests/             unit + integration (pytest)

frontend/      Next.js 14 App Router + Tailwind v3 + TypeScript
  app/
    login/                                sign in
    projects/                             project list
    projects/[id]/                        project dashboard
    projects/[id]/import/                 add candidates (paste / upload)
    projects/[id]/candidates/[id]/        candidate detail + evidence
    projects/[id]/compare/                side-by-side comparison
  lib/           api client + auth helpers

docs/          architecture, data model, API design, AI features, presentation notes
```

---

## Backend — modules at a glance

`backend/app/services/`:

| Service | What it does |
|---|---|
| `extraction_service` | Normalize raw listing input into the candidate schema |
| `ocr_service` | OCR for image and PDF listings |
| `file_storage_service` | Store uploaded sources (local FS / S3-compatible) |
| `candidate_import_service` + `_background_service` | Parse input, enqueue extraction, persist candidate |
| `candidate_pipeline_service` | Orchestrate assessment steps after import |
| `candidate_assessment_service` | Top-level assessment entry point |
| `benchmark_service` | Match candidate to SDU district/size benchmark (rent reasonableness) |
| `cost_assessment_service` | Rent + management + rates + estimated bills total |
| `clause_assessment_service` | Deposit, early termination, repairs, agency-fee checks |
| `priority_service` | Scoring used by the dashboard |
| `investigation_service` | Open questions / things to verify next |
| `comparison_service` + `comparison_briefing_service` | Side-by-side data + natural-language briefing |
| `dashboard_service` | Project-level summary numbers |

`backend/app/integrations/`:

- `llm/` — LLM provider wrapper + shared prompt templates.

---

## Frontend — pages at a glance

| Route | Purpose |
|---|---|
| `/` | Landing page |
| `/login` | Sign in |
| `/projects` | List of search projects (create / delete) |
| `/projects/[id]` | Project dashboard: KPIs + candidate grid |
| `/projects/[id]/import` | Add a new candidate (paste text / upload files) |
| `/projects/[id]/candidates/[id]` | One candidate's extracted fields + evidence + investigation items |
| `/projects/[id]/compare` | Compare 2–5 selected candidates |

---

## Setup

### Prerequisites

- Python 3.11+
- Node.js 20+
- PostgreSQL 15+ (local or Neon / Supabase)

### Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt

cp .env.example .env
# edit .env — see "Environment variables" below

alembic upgrade head
uvicorn app.main:app --reload
# http://127.0.0.1:8000  (docs: /docs)
```

### Frontend

```bash
cd frontend
npm install
cp .env.local.example .env.local
# edit NEXT_PUBLIC_API_BASE_URL if backend isn't on :8000
npm run dev
# http://localhost:3000
```

### Environment variables

**Backend** (`backend/.env`):

Required:
- `DATABASE_URL` — e.g. `postgresql+asyncpg://user:pass@host:5432/rentwise`
- `SECRET_KEY` — JWT signing key (generate with `openssl rand -hex 32`)
- `OPENAI_API_KEY` **or** `ANTHROPIC_API_KEY` — pick your LLM provider

Optional:
- `LLM_PROVIDER` — `openai` or `anthropic` (default: `openai`)
- `LLM_MODEL` — override the default model for the chosen provider
- `ALLOWED_ORIGINS` — CORS whitelist, comma-separated
- `STORAGE_BACKEND` — `local` (default) or `s3`
- `S3_BUCKET` / `S3_REGION` / `S3_ACCESS_KEY` / `S3_SECRET_KEY` — required if `STORAGE_BACKEND=s3`

**Frontend** (`frontend/.env.local`):

- `NEXT_PUBLIC_API_BASE_URL` — e.g. `http://localhost:8000`

---

## Testing

```bash
# Backend
cd backend
pytest                    # unit + integration
pytest tests/unit/        # unit only (faster)

# Frontend
cd frontend
npm run lint
npx next build            # type check + production build
```

Integration tests require `DATABASE_URL` to point at a real PostgreSQL
instance. Unit tests are DB-free.

---

## Data safety

- Passwords: bcrypt.
- JWT: HS256, signed with `SECRET_KEY`.
- Candidate source files: stored under the user+project namespace; access
  requires the user's JWT.
- No third-party tracking. LLM requests go directly from the backend to
  OpenAI/Anthropic with the user's prompt; no data brokering layer.

---

## Evidence layers

| Layer | Status | Notes |
|---|---|---|
| SDU rent benchmark | Active | District × size rent bands from a bundled JSON (HK SDU survey data) |
| Cost breakdown | Active | Rent + management + rates + estimated utilities |
| Clause flags | Active | Deposit, early termination, agency fee, repairs, pets |
| Investigation items | Active | Per-candidate open questions |
| Commute evidence | **Designed, not yet implemented** | See `docs/superpowers/specs/2026-04-05-single-destination-commute-design.md` |
| Tenancy-law RAG | Roadmap | Retrieval over HK Landlord & Tenant Ordinance |

---

## Phase status

- **Phase 1** — Candidate pool, extraction, import, dashboard. Complete.
- **Phase 2** — Per-candidate assessment (benchmark, cost, clauses, priority),
  compare view with briefing, investigation items. Complete.
- **Phase 2.5** — Agent refinements, better extraction for messy inputs,
  compare-briefing polish. Active in this submission.
- **Phase 3** — Commute evidence, UI redesign, tenancy-law RAG. Planned; see
  design docs under `docs/`.

---

## Deployment (reference)

The project deploys cleanly on:

- **Frontend**: Vercel (Next.js App Router).
- **Backend**: Render / Railway / Fly.io (uvicorn + Alembic migrate on start).
- **Database**: Neon or Supabase (PostgreSQL with async-friendly connection string).

Set `ALLOWED_ORIGINS` on the backend to the frontend's deployed URL and
`NEXT_PUBLIC_API_BASE_URL` on the frontend to the backend's deployed URL.

---

## Docs

- `docs/overview.md` — product overview
- `docs/architecture.md` — high-level architecture
- `docs/data-model.md` — database schema
- `docs/api-design.md` — REST API contract
- `docs/ai-features.md` — how the LLM is used across services
- `docs/presentation-notes.md` — submission presentation notes
- `docs/refactor/implementation-spec-v2.md` — internal refactor spec
- `docs/superpowers/specs/2026-04-05-single-destination-commute-design.md` — commute feature design (not yet implemented in this submission)

---

## License

Coursework submission. All rights reserved by the author.
