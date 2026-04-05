# RentWise Refactor and Compare Implementation Specification

**Version**: 2.2  
**Date**: 2026-04-02  
**Status**: Phase 1 stabilized, Phase 2 compare MVP active

---

## Overview

This document tracks the refactoring of RentWise from a Streamlit monolith to a monorepo architecture with a FastAPI backend and Next.js frontend, and the first compare-oriented Phase 2 product layer built on top of that foundation.

## Architecture

### Monorepo Structure

```text
RentWise/
|- backend/   # FastAPI + SQLAlchemy + Pydantic v2 + LangGraph
|- frontend/  # Next.js + React + TypeScript + Tailwind CSS
|- legacy/    # Original Streamlit code (reference only)
`- docs/      # Documentation
```

### Key Design Decisions

1. Async SQLAlchemy with `asyncpg` for PostgreSQL.
2. JWT authentication with browser-side token storage in Phase 1.
3. Tailwind CSS for the frontend UI layer.
4. LangGraph for lightweight investigation workflow orchestration.
5. Candidate pool plus decision progression as the core product model.

---

## Data Models

### Core Entities

| Entity | Description |
|--------|-------------|
| User | User accounts with JWT auth |
| SearchProject | Rental search project |
| CandidateListing | Candidate rental listing |
| CandidateExtractedInfo | Structured info extracted from text |
| CostAssessment | Cost analysis results |
| ClauseAssessment | Clause analysis results |
| CandidateAssessment | Overall assessment |
| InvestigationItem | Items to investigate |

Phase 2 compare MVP does not add a persisted compare table. Compare results are computed on demand from the selected candidate set.

### Status Enumerations

**CandidateListing.status**
- `new`
- `needs_info`
- `follow_up`
- `high_risk_pending`
- `recommended_reject`
- `shortlisted`

**CandidateListing.user_decision**
- `undecided`
- `shortlisted`
- `rejected`

---

## API Endpoints

### Auth
- `POST /api/v1/auth/register`
- `POST /api/v1/auth/login`
- `GET /api/v1/auth/me`

### Projects
- `POST /api/v1/projects`
- `GET /api/v1/projects`
- `GET /api/v1/projects/{id}`
- `PUT /api/v1/projects/{id}`
- `DELETE /api/v1/projects/{id}`

### Candidates
- `POST /api/v1/projects/{id}/candidates/import`
- `GET /api/v1/projects/{id}/candidates`
- `GET /api/v1/projects/{id}/candidates/{candidateId}`
- `PUT /api/v1/projects/{id}/candidates/{candidateId}`
- `POST /api/v1/projects/{id}/candidates/{candidateId}/reassess`
- `POST /api/v1/projects/{id}/candidates/{candidateId}/shortlist`
- `POST /api/v1/projects/{id}/candidates/{candidateId}/reject`

### Dashboard
- `GET /api/v1/projects/{id}/dashboard`

### Investigation
- `POST /api/v1/projects/{id}/investigation/run`
- `GET /api/v1/projects/{id}/investigation/current`

### Comparison
- `POST /api/v1/projects/{id}/compare`

---

## Services

### ExtractionService
Extracts structured information from raw text using the configured LLM provider.  
If no user-supplied candidate name is provided, the import flow can auto-generate a smart name after extraction.

### CostAssessmentService
Analyzes cost information with hard rules:
- Unknown fees are never treated as zero.
- Only knowing the quoted rent does not qualify as high confidence.
- Cost uncertainty prevents a high-confidence recommendation.

### ClauseAssessmentService
Analyzes lease terms, move-in timing, and repair responsibility.

### CandidateAssessmentService
Generates overall assessment with hard rules:
- Critical cost missing means no high-confidence recommendation.
- Critical clause uncertainty means no high-confidence recommendation.
- Hard user constraint violations can lead to reject.
- High potential but key unknowns lead to `verify_cost` or `verify_clause`, not direct recommendation.

### PriorityService
Ranks candidates by action priority, not by shortlist status.

### DashboardService
Aggregates stats, action-oriented priority reasons, and investigation checklist items.

### ComparisonService
Builds a shortlist decision workspace from a user-selected candidate set:
- decision snapshot
- grouped compare result
- key differences
- recommended next actions
- explanation-focused candidate compare cards

---

## Frontend Pages

| Route | Purpose |
|-------|---------|
| `/login` | Login and registration |
| `/projects` | Project list, creation, and deletion |
| `/projects/[id]` | Dashboard with advice, stats, priorities, suggested compare preview, and all candidates |
| `/projects/[id]/import` | Import candidate via text |
| `/projects/[id]/candidates/[candidateId]` | Candidate detail with assessment, editing, actions, and compare context |
| `/projects/[id]/compare` | Compare workspace for grouped shortlist decisions |

---

## Environment Variables

### Backend (`.env`)

```env
SECRET_KEY=your-secret-key-min-16-chars
DATABASE_URL=postgresql+asyncpg://user:pass@localhost:5432/rentwise
LLM_PROVIDER=groq
GROQ_API_KEY=your-groq-key
GROQ_MODEL=llama-3.3-70b-versatile
OLLAMA_HOST=http://localhost:11434
OLLAMA_API_KEY=your-ollama-key
OLLAMA_MODEL=llama3.3
```

### Frontend (`.env.local`)

```env
NEXT_PUBLIC_API_URL=http://localhost:8000
```

---

## Startup Commands

### Backend

```bash
cd backend
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload --port 8000
```

If your local database was previously created by the old startup `create_all()` flow, align Alembic first:

```bash
alembic stamp head
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

---

## Verification Checklist

- [x] User can register and log in
- [x] User can create a Search Project
- [x] User can delete a Search Project
- [x] User can import a text-based candidate
- [x] Candidate import generates assessments
- [x] Candidate import can auto-generate a smart name
- [x] Dashboard shows stats and priorities
- [x] Candidate detail shows assessments
- [x] Candidate detail supports editing and reassessment
- [x] User can shortlist or reject a candidate
- [x] Alembic manages schema migrations
- [x] Real PostgreSQL-backed integration test exists
- [x] Legacy code is isolated in `legacy/streamlit_app/`
- [x] Dashboard supports manual compare-set selection
- [x] Compare workspace groups selected candidates by decision readiness
- [x] Compare workspace explains tradeoffs and blockers
- [x] Dashboard can surface a suggested compare set
- [x] Candidate detail can surface compare context for the current candidate

---

## Notes

- Dashboard summary is generated on demand and is not persisted.
- Investigation items are regenerated each run.
- Compare results are generated on demand and are not persisted.
- Compare aims to support a shortlist decision workflow, not a fake exact ranking workflow.
- Explanation is treated as a first-class output in compare:
  - why the candidate is in this group
  - main tradeoff
  - open blocker
  - next action
- No Docker in Phase 1.
- No WebSocket in Phase 1.
- No OCR or image upload in Phase 1.
- No RAG main flow in Phase 1.
