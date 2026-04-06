from __future__ import annotations

import sys
from pathlib import Path
from unittest import TestCase

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.services.candidate_assessment_service import CandidateAssessmentService
from tests.helpers import build_candidate, build_project, build_user


class CandidateAssessmentServiceTests(TestCase):
    def setUp(self) -> None:
        self.service = CandidateAssessmentService()
        self.user = build_user()
        self.project = build_project(self.user)

    def test_trust_signal_raises_decision_risk_and_verify_clause_action(self):
        candidate = build_candidate(self.project)
        candidate.extracted_info.decision_signals = [
            {
                "key": "holding_fee_risk",
                "category": "trust",
                "label": "Holding money refund is unclear",
                "source": "chat",
                "evidence": "If u don't like after viewing I give back (maybe).",
                "note": "Needs written confirmation.",
            }
        ]
        candidate.cost_assessment.monthly_cost_confidence = "high"
        candidate.cost_assessment.known_monthly_cost = 18000
        candidate.cost_assessment.cost_risk_flag = "none"
        candidate.clause_assessment.clause_confidence = "high"
        candidate.clause_assessment.clause_risk_flag = "none"

        assessment = self.service.assess(
            extracted_info=candidate.extracted_info,
            cost_assessment=candidate.cost_assessment,
            clause_assessment=candidate.clause_assessment,
            max_budget=self.project.max_budget,
            preferred_districts=self.project.preferred_districts,
            must_have=self.project.must_have,
            deal_breakers=self.project.deal_breakers,
            move_in_target=self.project.move_in_target,
        )

        self.assertEqual(assessment.decision_risk_level, "high")
        self.assertEqual(assessment.next_best_action, "verify_clause")
        self.assertIn("Trust concern", assessment.labels)

    def test_shared_bathroom_signal_can_trigger_hard_conflict(self):
        candidate = build_candidate(self.project)
        candidate.extracted_info.decision_signals = [
            {
                "key": "bathroom_sharing",
                "category": "living_arrangement",
                "label": "Shared bathroom with one other tenant",
                "source": "chat",
                "evidence": "Share with one person only.",
                "note": "",
            }
        ]

        assessment = self.service.assess(
            extracted_info=candidate.extracted_info,
            cost_assessment=candidate.cost_assessment,
            clause_assessment=candidate.clause_assessment,
            max_budget=self.project.max_budget,
            preferred_districts=self.project.preferred_districts,
            must_have=self.project.must_have,
            deal_breakers=self.project.deal_breakers,
            move_in_target=self.project.move_in_target,
        )

        self.assertEqual(assessment.next_best_action, "reject")
        self.assertIn("Hard conflict", assessment.labels)
