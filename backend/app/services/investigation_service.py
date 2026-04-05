"""Investigation workflow service."""

from __future__ import annotations

from ..agent.investigation_graph import investigation_graph


class InvestigationService:
    """Runs the lightweight investigation workflow."""

    async def run(self, project, candidates):
        """Run the graph and return the latest dashboard-oriented state."""
        initial_state = {
            "project": project,
            "candidates": candidates,
            "priority_candidates": [],
            "open_items": [],
            "current_advice": "",
        }
        return await investigation_graph.ainvoke(initial_state)
