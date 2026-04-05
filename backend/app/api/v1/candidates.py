"""Candidates API endpoints."""

from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ...db.database import get_db
from ...db.models import CandidateListing, SearchProject, User
from ...schemas.candidate import CandidateImport, CandidateListResponse, CandidateResponse, CandidateUpdate
from ...services.benchmark_service import BenchmarkService
from ...services.candidate_pipeline_service import CandidatePipelineService
from .auth import get_current_user

router = APIRouter()
pipeline_service = CandidatePipelineService()
benchmark_service = BenchmarkService()


async def get_project_for_user(project_id: UUID, user: User, db: AsyncSession) -> SearchProject:
    """Get a project owned by the current user."""
    result = await db.execute(
        select(SearchProject).where(
            SearchProject.id == project_id,
            SearchProject.user_id == user.id,
        )
    )
    project = result.scalar_one_or_none()
    if project is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


def _candidate_detail_query():
    return (
        select(CandidateListing)
        .options(
            selectinload(CandidateListing.extracted_info),
            selectinload(CandidateListing.cost_assessment),
            selectinload(CandidateListing.clause_assessment),
            selectinload(CandidateListing.candidate_assessment),
        )
    )


def _serialize_candidate(candidate: CandidateListing) -> CandidateResponse:
    response = CandidateResponse.model_validate(candidate)
    return response.model_copy(update={"benchmark": benchmark_service.build_for_candidate(candidate)})


async def get_candidate_for_project_user(
    project_id: UUID,
    candidate_id: UUID,
    user: User,
    db: AsyncSession,
) -> tuple[SearchProject, CandidateListing]:
    """Get a candidate belonging to a project owned by the current user."""
    project = await get_project_for_user(project_id, user, db)
    result = await db.execute(
        _candidate_detail_query().where(
            CandidateListing.id == candidate_id,
            CandidateListing.project_id == project.id,
        )
    )
    candidate = result.scalar_one_or_none()
    if candidate is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Candidate not found")
    return project, candidate


@router.post("/projects/{project_id}/candidates/import", response_model=CandidateResponse, status_code=status.HTTP_201_CREATED)
async def import_candidate(
    project_id: UUID,
    candidate_data: CandidateImport,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Import a new candidate listing and immediately assess it."""
    project = await get_project_for_user(project_id, current_user, db)

    combined_text = "\n".join(
        part.strip()
        for part in [
            candidate_data.raw_listing_text or "",
            candidate_data.raw_chat_text or "",
            candidate_data.raw_note_text or "",
        ]
        if part and part.strip()
    ) or None

    if not combined_text:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="At least one text field is required")

    name = candidate_data.name
    should_autoname = not name
    if not name:
        count_result = await db.execute(select(func.count()).where(CandidateListing.project_id == project.id))
        name = f"Candidate {int(count_result.scalar() or 0) + 1}"

    candidate = CandidateListing(
        project_id=project.id,
        name=name,
        source_type=candidate_data.source_type,
        raw_listing_text=candidate_data.raw_listing_text,
        raw_chat_text=candidate_data.raw_chat_text,
        raw_note_text=candidate_data.raw_note_text,
        combined_text=combined_text,
    )
    db.add(candidate)
    await db.flush()

    await pipeline_service.assess_candidate(db=db, project=project, candidate=candidate)
    if should_autoname:
        candidate.name = await pipeline_service.generate_candidate_name(candidate)
    await db.flush()

    _, candidate = await get_candidate_for_project_user(project.id, candidate.id, current_user, db)
    return _serialize_candidate(candidate)


@router.get("/projects/{project_id}/candidates", response_model=CandidateListResponse)
async def list_candidates(
    project_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List candidates for a project."""
    project = await get_project_for_user(project_id, current_user, db)
    count_result = await db.execute(select(func.count()).where(CandidateListing.project_id == project.id))
    total = count_result.scalar() or 0

    result = await db.execute(
        _candidate_detail_query()
        .where(CandidateListing.project_id == project.id)
        .order_by(CandidateListing.updated_at.desc())
    )
    candidates = result.scalars().all()
    return CandidateListResponse(
        candidates=[_serialize_candidate(candidate) for candidate in candidates],
        total=total,
    )


@router.get("/projects/{project_id}/candidates/{candidate_id}", response_model=CandidateResponse)
async def get_candidate(
    project_id: UUID,
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a candidate by ID."""
    _, candidate = await get_candidate_for_project_user(project_id, candidate_id, current_user, db)
    return _serialize_candidate(candidate)


@router.put("/projects/{project_id}/candidates/{candidate_id}", response_model=CandidateResponse)
async def update_candidate(
    project_id: UUID,
    candidate_id: UUID,
    candidate_data: CandidateUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Update candidate content and rerun assessments when text changes."""
    project, candidate = await get_candidate_for_project_user(project_id, candidate_id, current_user, db)

    update_data = candidate_data.model_dump(exclude_unset=True)
    text_fields = {"raw_listing_text", "raw_chat_text", "raw_note_text"}
    should_reassess = any(field in update_data for field in text_fields)

    for field, value in update_data.items():
        setattr(candidate, field, value)

    if should_reassess:
        candidate.combined_text = "\n".join(
            part.strip()
            for part in [
                candidate.raw_listing_text or "",
                candidate.raw_chat_text or "",
                candidate.raw_note_text or "",
            ]
            if part and part.strip()
        ) or None
        if not candidate.combined_text:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="At least one text field is required",
            )
        await pipeline_service.assess_candidate(db=db, project=project, candidate=candidate)

    await db.flush()
    _, candidate = await get_candidate_for_project_user(project.id, candidate.id, current_user, db)
    return _serialize_candidate(candidate)


@router.post("/projects/{project_id}/candidates/{candidate_id}/reassess", response_model=CandidateResponse)
async def reassess_candidate(
    project_id: UUID,
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Rerun assessments for a candidate."""
    project, candidate = await get_candidate_for_project_user(project_id, candidate_id, current_user, db)
    await pipeline_service.assess_candidate(db=db, project=project, candidate=candidate)
    await db.flush()
    _, candidate = await get_candidate_for_project_user(project.id, candidate.id, current_user, db)
    return _serialize_candidate(candidate)


@router.post("/projects/{project_id}/candidates/{candidate_id}/shortlist", response_model=CandidateResponse)
async def shortlist_candidate(
    project_id: UUID,
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Shortlist a candidate."""
    project, candidate = await get_candidate_for_project_user(project_id, candidate_id, current_user, db)
    candidate.user_decision = "shortlisted"
    candidate.status = "shortlisted"
    if candidate.candidate_assessment is not None:
        candidate.candidate_assessment.status = "shortlisted"
    await db.flush()
    _, candidate = await get_candidate_for_project_user(project.id, candidate.id, current_user, db)
    return _serialize_candidate(candidate)


@router.post("/projects/{project_id}/candidates/{candidate_id}/reject", response_model=CandidateResponse)
async def reject_candidate(
    project_id: UUID,
    candidate_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Reject a candidate."""
    project, candidate = await get_candidate_for_project_user(project_id, candidate_id, current_user, db)
    candidate.user_decision = "rejected"
    candidate.status = "recommended_reject"
    if candidate.candidate_assessment is not None:
        candidate.candidate_assessment.status = "recommended_reject"
    await db.flush()
    _, candidate = await get_candidate_for_project_user(project.id, candidate.id, current_user, db)
    return _serialize_candidate(candidate)
