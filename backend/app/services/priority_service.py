"""Priority service for ranking candidates by next-best work."""

from __future__ import annotations

from typing import List
from uuid import UUID

from ..db.models import CandidateAssessment

LEVEL_SCORES = {
    "high": 3,
    "medium": 2,
    "low": 1,
}

ACTION_BASE_SCORES = {
    "verify_cost": 90.0,
    "verify_clause": 82.0,
    "schedule_viewing": 72.0,
    "keep_warm": 56.0,
    "reject": 28.0,
}


class PriorityService:
    """Rank candidates by what is most worth handling now."""

    def rank(self, assessments: List[CandidateAssessment]) -> List[tuple[UUID, float]]:
        """Return candidates sorted by action-oriented priority."""
        scored = [(assessment.candidate_id, self._calculate_score(assessment)) for assessment in assessments]
        scored.sort(key=lambda item: item[1], reverse=True)
        return scored

    def get_top_n(self, assessments: List[CandidateAssessment], n: int = 3) -> List[UUID]:
        """Get top N candidate IDs by current handling priority."""
        return [candidate_id for candidate_id, _score in self.rank(assessments)[:n]]

    def _calculate_score(self, assessment: CandidateAssessment) -> float:
        action_score = ACTION_BASE_SCORES.get(assessment.next_best_action, 40.0)
        potential_score = LEVEL_SCORES.get(assessment.potential_value_level, 1)
        info_gain_score = LEVEL_SCORES.get(assessment.information_gain_level, 1)
        confidence_score = LEVEL_SCORES.get(assessment.recommendation_confidence, 1)
        risk_score = LEVEL_SCORES.get(assessment.decision_risk_level, 1)
        uncertainty_score = LEVEL_SCORES.get(assessment.critical_uncertainty_level, 1)
        completeness_score = LEVEL_SCORES.get(assessment.completeness_level, 1)

        total = action_score
        total += potential_score * 5.0
        total += info_gain_score * 4.0

        if assessment.next_best_action == "verify_cost":
            total += uncertainty_score * 3.0
            total += risk_score * 1.5
            total -= confidence_score * 1.0
        elif assessment.next_best_action == "verify_clause":
            total += uncertainty_score * 2.5
            total += risk_score * 2.5
            total -= confidence_score * 0.5
        elif assessment.next_best_action == "schedule_viewing":
            total += confidence_score * 4.0
            total += completeness_score * 2.0
            total -= risk_score * 1.5
        elif assessment.next_best_action == "keep_warm":
            total += confidence_score * 1.5
            total += completeness_score * 1.5
            total -= uncertainty_score * 1.0
        elif assessment.next_best_action == "reject":
            total += risk_score * 1.5
            total -= potential_score * 2.0

        return round(total, 2)
