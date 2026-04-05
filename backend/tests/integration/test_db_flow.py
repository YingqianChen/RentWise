from __future__ import annotations

import asyncio
import os
import sys
import uuid
from pathlib import Path
from unittest import SkipTest, TestCase

from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import delete
from sqlalchemy import text as sa_text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.core.config import settings
from app.db.models import User
from app.main import app


class DatabaseFlowTests(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        super().setUpClass()
        if os.getenv("RUN_DB_INTEGRATION") != "1":
            raise SkipTest("Set RUN_DB_INTEGRATION=1 to run real database integration tests.")

        alembic_cfg = Config(str(Path(__file__).resolve().parents[2] / "alembic.ini"))
        users_exists, alembic_version_exists = asyncio.run(cls._inspect_schema_state())
        if users_exists and not alembic_version_exists:
            command.stamp(alembic_cfg, "head")
        else:
            command.upgrade(alembic_cfg, "head")

    def setUp(self) -> None:
        self.email = f"db-flow-{uuid.uuid4().hex[:12]}@example.com"

    def tearDown(self) -> None:
        asyncio.run(self._cleanup_user())

    async def _cleanup_user(self) -> None:
        engine = create_async_engine(settings.DATABASE_URL, future=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            await session.execute(delete(User).where(User.email == self.email))
            await session.commit()
        await engine.dispose()

    @staticmethod
    async def _inspect_schema_state() -> tuple[bool, bool]:
        engine = create_async_engine(settings.DATABASE_URL, future=True)
        session_factory = async_sessionmaker(engine, expire_on_commit=False)
        async with session_factory() as session:
            users_exists = await session.scalar(sa_text("SELECT to_regclass('public.users')"))
            alembic_version_exists = await session.scalar(
                sa_text("SELECT to_regclass('public.alembic_version')")
            )
        await engine.dispose()
        return bool(users_exists), bool(alembic_version_exists)

    def test_register_create_project_import_candidate_and_fetch_dashboard(self) -> None:
        with TestClient(app) as client:
            register_response = client.post(
                "/api/v1/auth/register",
                json={"email": self.email, "password": "db-flow-password"},
            )
            self.assertEqual(register_response.status_code, 201, register_response.text)
            token = register_response.json()["access_token"]
            headers = {"Authorization": f"Bearer {token}"}

            project_response = client.post(
                "/api/v1/projects",
                headers=headers,
                json={
                    "title": "DB Flow Project",
                    "max_budget": 22000,
                    "preferred_districts": ["Wan Chai"],
                    "must_have": ["furnished"],
                    "deal_breakers": ["shared bathroom"],
                },
            )
            self.assertEqual(project_response.status_code, 201, project_response.text)
            project_id = project_response.json()["id"]

            candidate_response = client.post(
                f"/api/v1/projects/{project_id}/candidates/import",
                headers=headers,
                json={
                    "name": "DB Flow Candidate",
                    "raw_listing_text": "Wan Chai flat, rent 18000, deposit 2 months, lease 2 years.",
                    "raw_chat_text": "Agent says management fee may be separate.",
                },
            )
            self.assertEqual(candidate_response.status_code, 201, candidate_response.text)
            candidate_payload = candidate_response.json()
            self.assertEqual(candidate_payload["name"], "DB Flow Candidate")
            self.assertIsNotNone(candidate_payload["candidate_assessment"])

            dashboard_response = client.get(
                f"/api/v1/projects/{project_id}/dashboard",
                headers=headers,
            )
            self.assertEqual(dashboard_response.status_code, 200, dashboard_response.text)
            dashboard_payload = dashboard_response.json()

            self.assertEqual(dashboard_payload["project_id"], project_id)
            self.assertGreaterEqual(dashboard_payload["stats"]["total"], 1)
            self.assertTrue(dashboard_payload["current_advice"])
            self.assertGreaterEqual(len(dashboard_payload["priority_candidates"]), 1)
