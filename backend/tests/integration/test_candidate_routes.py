from __future__ import annotations

import sys
import uuid
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock, patch

from fastapi import HTTPException

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.api.v1 import candidates as candidates_api
from app.schemas.candidate import CandidateImport
from tests.helpers import build_candidate, build_project, build_user


class _ScalarResult:
    def __init__(self, value):
        self._value = value

    def scalar(self):
        return self._value

    def scalar_one_or_none(self):
        return self._value


class FakeAsyncSession:
    def __init__(self, execute_results=None):
        self.execute_results = list(execute_results or [])
        self.added = []
        self.flush = AsyncMock()

    async def execute(self, *_args, **_kwargs):
        if not self.execute_results:
            raise AssertionError("Unexpected execute() call in test")
        return self.execute_results.pop(0)

    def add(self, obj):
        self.added.append(obj)
        if getattr(obj, "id", None) is None:
            obj.id = uuid.uuid4()


class CandidateRouteTests(IsolatedAsyncioTestCase):
    async def test_import_candidate_runs_pipeline_and_returns_assessment(self):
        user = build_user()
        project = build_project(user)
        db = FakeAsyncSession(execute_results=[_ScalarResult(0)])
        detailed_candidate = build_candidate(project, name="Candidate 1")
        assess_mock = AsyncMock()

        async def fake_generate_candidate_name(_candidate):
            detailed_candidate.name = "Wan Chai $18000"
            return detailed_candidate.name

        async def fake_get_project_for_user(project_id, current_user, session):
            self.assertEqual(project_id, project.id)
            self.assertEqual(current_user.id, user.id)
            self.assertIs(session, db)
            return project

        async def fake_get_candidate_for_project_user(project_id, candidate_id, current_user, session):
            self.assertEqual(project_id, project.id)
            self.assertEqual(current_user.id, user.id)
            self.assertIs(session, db)
            detailed_candidate.id = candidate_id
            detailed_candidate.project_id = project_id
            return project, detailed_candidate

        with (
            patch.object(candidates_api, "get_project_for_user", fake_get_project_for_user),
            patch.object(candidates_api, "get_candidate_for_project_user", fake_get_candidate_for_project_user),
            patch.object(candidates_api.pipeline_service, "assess_candidate", assess_mock),
            patch.object(candidates_api.pipeline_service, "generate_candidate_name", fake_generate_candidate_name),
        ):
            response = await candidates_api.import_candidate(
                project_id=project.id,
                candidate_data=CandidateImport(raw_listing_text="Rent 18000 in Wan Chai"),
                current_user=user,
                db=db,
            )

        self.assertEqual(response.project_id, project.id)
        self.assertEqual(response.name, "Wan Chai $18000")
        self.assertIsNotNone(response.candidate_assessment)
        assess_mock.assert_awaited_once()

    async def test_import_candidate_keeps_user_supplied_name(self):
        user = build_user()
        project = build_project(user)
        db = FakeAsyncSession()
        detailed_candidate = build_candidate(project, name="User title")
        assess_mock = AsyncMock()
        name_mock = AsyncMock(return_value="Should not be used")

        async def fake_get_project_for_user(project_id, current_user, session):
            return project

        async def fake_get_candidate_for_project_user(project_id, candidate_id, current_user, session):
            detailed_candidate.id = candidate_id
            detailed_candidate.project_id = project_id
            detailed_candidate.name = "User title"
            return project, detailed_candidate

        with (
            patch.object(candidates_api, "get_project_for_user", fake_get_project_for_user),
            patch.object(candidates_api, "get_candidate_for_project_user", fake_get_candidate_for_project_user),
            patch.object(candidates_api.pipeline_service, "assess_candidate", assess_mock),
            patch.object(candidates_api.pipeline_service, "generate_candidate_name", name_mock),
        ):
            response = await candidates_api.import_candidate(
                project_id=project.id,
                candidate_data=CandidateImport(name="User title", raw_listing_text="Rent 18000 in Wan Chai"),
                current_user=user,
                db=db,
            )

        self.assertEqual(response.name, "User title")
        assess_mock.assert_awaited_once()
        name_mock.assert_not_awaited()

    async def test_reassess_candidate_runs_pipeline(self):
        user = build_user()
        project = build_project(user)
        candidate = build_candidate(project)
        db = FakeAsyncSession()
        assess_mock = AsyncMock()

        async def fake_get_candidate_for_project_user(project_id, candidate_id, current_user, session):
            self.assertEqual(project_id, project.id)
            self.assertEqual(candidate_id, candidate.id)
            self.assertEqual(current_user.id, user.id)
            self.assertIs(session, db)
            return project, candidate

        with (
            patch.object(candidates_api, "get_candidate_for_project_user", fake_get_candidate_for_project_user),
            patch.object(candidates_api.pipeline_service, "assess_candidate", assess_mock),
        ):
            response = await candidates_api.reassess_candidate(
                project_id=project.id,
                candidate_id=candidate.id,
                current_user=user,
                db=db,
            )

        self.assertEqual(response.id, candidate.id)
        assess_mock.assert_awaited_once_with(db=db, project=project, candidate=candidate)
        db.flush.assert_awaited_once()

    async def test_update_candidate_with_text_changes_reruns_pipeline(self):
        user = build_user()
        project = build_project(user)
        candidate = build_candidate(project)
        db = FakeAsyncSession()
        assess_mock = AsyncMock()

        async def fake_get_candidate_for_project_user(project_id, candidate_id, current_user, session):
            self.assertEqual(project_id, project.id)
            self.assertEqual(candidate_id, candidate.id)
            self.assertEqual(current_user.id, user.id)
            self.assertIs(session, db)
            return project, candidate

        with (
            patch.object(candidates_api, "get_candidate_for_project_user", fake_get_candidate_for_project_user),
            patch.object(candidates_api.pipeline_service, "assess_candidate", assess_mock),
        ):
            response = await candidates_api.update_candidate(
                project_id=project.id,
                candidate_id=candidate.id,
                candidate_data=candidates_api.CandidateUpdate(
                    raw_listing_text="Updated listing text",
                    raw_chat_text="Updated chat text",
                ),
                current_user=user,
                db=db,
            )

        self.assertEqual(response.id, candidate.id)
        self.assertEqual(candidate.raw_listing_text, "Updated listing text")
        self.assertEqual(candidate.raw_chat_text, "Updated chat text")
        self.assertIn("Updated listing text", candidate.combined_text)
        assess_mock.assert_awaited_once_with(db=db, project=project, candidate=candidate)
        db.flush.assert_awaited_once()

    async def test_update_candidate_rejects_empty_text_payload(self):
        user = build_user()
        project = build_project(user)
        candidate = build_candidate(project)
        db = FakeAsyncSession()
        assess_mock = AsyncMock()

        async def fake_get_candidate_for_project_user(project_id, candidate_id, current_user, session):
            return project, candidate

        with (
            patch.object(candidates_api, "get_candidate_for_project_user", fake_get_candidate_for_project_user),
            patch.object(candidates_api.pipeline_service, "assess_candidate", assess_mock),
        ):
            with self.assertRaises(HTTPException) as exc_info:
                await candidates_api.update_candidate(
                    project_id=project.id,
                    candidate_id=candidate.id,
                    candidate_data=candidates_api.CandidateUpdate(
                        raw_listing_text="",
                        raw_chat_text="",
                        raw_note_text="",
                    ),
                    current_user=user,
                    db=db,
                )

        self.assertEqual(exc_info.exception.status_code, 400)
        self.assertEqual(exc_info.exception.detail, "At least one text field is required")
        assess_mock.assert_not_awaited()

    async def test_get_candidate_for_project_user_blocks_cross_project_candidate(self):
        user = build_user()
        project = build_project(user)
        db = FakeAsyncSession(execute_results=[_ScalarResult(None)])

        async def fake_get_project_for_user(project_id, current_user, session):
            self.assertEqual(project_id, project.id)
            self.assertEqual(current_user.id, user.id)
            self.assertIs(session, db)
            return project

        with patch.object(candidates_api, "get_project_for_user", fake_get_project_for_user):
            with self.assertRaises(HTTPException) as exc_info:
                await candidates_api.get_candidate_for_project_user(
                    project_id=project.id,
                    candidate_id=uuid.uuid4(),
                    user=user,
                    db=db,
                )

        self.assertEqual(exc_info.exception.status_code, 404)
        self.assertEqual(exc_info.exception.detail, "Candidate not found")
