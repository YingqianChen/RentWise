from __future__ import annotations

import sys
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.comparison_briefing_service import ComparisonBriefingService
from app.services.comparison_service import ComparisonService
from tests.helpers import build_candidate, build_project, build_user


class ComparisonBriefingServiceTests(IsolatedAsyncioTestCase):
    async def test_falls_back_to_deterministic_briefing_when_llm_fails(self):
        user = build_user()
        project = build_project(user)
        lead = build_candidate(project, name="Stable Lead", status="follow_up", next_best_action="schedule_viewing")
        lead.cost_assessment.monthly_cost_confidence = "high"
        lead.cost_assessment.cost_risk_flag = "none"
        lead.clause_assessment.clause_risk_flag = "none"
        lead.candidate_assessment.recommendation_confidence = "high"
        lead.candidate_assessment.critical_uncertainty_level = "low"

        compare_result = ComparisonService().compare(project, [lead, build_candidate(project, name="Needs Work")])
        service = ComparisonBriefingService()

        with patch("app.services.comparison_briefing_service.chat_completion_json", side_effect=RuntimeError("boom")):
            briefing = await service.build(
                project=project,
                candidates=[lead],
                summary=compare_result["summary"],
                groups=compare_result["groups"],
                key_differences=compare_result["key_differences"],
                recommended_actions=compare_result["recommended_next_actions"],
            )

        self.assertIn("current lead", briefing.current_take.lower())
        self.assertTrue(briefing.today_s_move)
        self.assertEqual(briefing.confidence_note, compare_result["summary"].confidence_note)

    async def test_uses_llm_fields_when_available(self):
        user = build_user()
        project = build_project(user)
        lead = build_candidate(project, name="Stable Lead", status="follow_up", next_best_action="schedule_viewing")
        compare_result = ComparisonService().compare(project, [lead, build_candidate(project, name="Needs Work")])
        service = ComparisonBriefingService()

        with patch(
            "app.services.comparison_briefing_service.chat_completion_json",
            return_value={
                "current_take": "Stable Lead is the easiest option to trust today.",
                "why_now": "Its cost and lease picture are clearer than the rest.",
                "what_could_change": "Needs Work could still move up if fee details are confirmed.",
                "today_s_move": "Push Stable Lead first and resolve one fee blocker on Needs Work.",
                "confidence_note": "The lead is real, but one missing cost detail could still reshape the shortlist.",
            },
        ):
            briefing = await service.build(
                project=project,
                candidates=[lead],
                summary=compare_result["summary"],
                groups=compare_result["groups"],
                key_differences=compare_result["key_differences"],
                recommended_actions=compare_result["recommended_next_actions"],
            )

        self.assertIn("trust", briefing.current_take.lower())
        self.assertIn("clearer", briefing.why_now.lower())
        self.assertIn("fee", briefing.what_could_change.lower())


if __name__ == "__main__":
    import unittest

    unittest.main()
