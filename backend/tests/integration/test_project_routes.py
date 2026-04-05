from __future__ import annotations

import sys
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import AsyncMock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.api.v1 import projects as projects_api
from tests.helpers import build_project, build_user


class FakeAsyncSession:
    def __init__(self):
        self.delete = AsyncMock()
        self.flush = AsyncMock()


class ProjectRouteTests(IsolatedAsyncioTestCase):
    async def test_delete_project_deletes_owned_project(self):
        user = build_user()
        project = build_project(user)
        db = FakeAsyncSession()

        async def fake_execute(*_args, **_kwargs):
            class _Result:
                @staticmethod
                def scalar_one_or_none():
                    return project

            return _Result()

        db.execute = fake_execute

        response = await projects_api.delete_project(
            project_id=project.id,
            current_user=user,
            db=db,
        )

        self.assertIsNone(response)
        db.delete.assert_awaited_once_with(project)
        db.flush.assert_awaited_once()
