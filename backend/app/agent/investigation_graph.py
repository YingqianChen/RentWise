"""Investigation workflow for dashboard summaries."""

from __future__ import annotations

from typing import Any, TypedDict

from ..services.dashboard_service import DashboardService

try:
    from langgraph.graph import END, StateGraph
except ImportError:  # pragma: no cover - exercised indirectly in lightweight envs
    END = None
    StateGraph = None


class InvestigationGraphState(TypedDict, total=False):
    project: Any
    candidates: list[Any]
    stats: Any
    priority_candidates: list[Any]
    open_items: list[Any]
    current_advice: str


dashboard_service = DashboardService()


def _assess_pool(state: InvestigationGraphState) -> InvestigationGraphState:
    return {"stats": dashboard_service.build_stats(state["candidates"])}


def _build_priority_queue(state: InvestigationGraphState) -> InvestigationGraphState:
    return {"priority_candidates": dashboard_service.build_priority_candidates(state["candidates"])}


def _generate_investigation_items(state: InvestigationGraphState) -> InvestigationGraphState:
    return {"open_items": dashboard_service.build_investigation_items(state["candidates"])}


def _synthesize_current_advice(state: InvestigationGraphState) -> InvestigationGraphState:
    return {
        "current_advice": dashboard_service.build_current_advice(
            project=state["project"],
            stats=state["stats"],
            priority_candidates=state["priority_candidates"],
            open_items=state["open_items"],
        )
    }


def _route_after_assess_pool(state: InvestigationGraphState) -> str:
    stats = state.get("stats")
    if not stats or getattr(stats, "total", 0) == 0:
        return "synthesize_current_advice"
    return "build_priority_queue"


def _route_after_priority_queue(state: InvestigationGraphState) -> str:
    if state.get("priority_candidates"):
        return "generate_investigation_items"
    return "synthesize_current_advice"


class _FallbackInvestigationGraph:
    """Fallback workflow when LangGraph is unavailable."""

    async def ainvoke(self, initial_state: InvestigationGraphState) -> InvestigationGraphState:
        state = dict(initial_state)
        for step in (
            _assess_pool,
            _build_priority_queue,
            _generate_investigation_items,
            _synthesize_current_advice,
        ):
            state.update(step(state))
        return state


def build_investigation_graph():
    """Build and compile the investigation graph when available."""
    if StateGraph is None:
        return _FallbackInvestigationGraph()

    graph = StateGraph(InvestigationGraphState)
    graph.add_node("assess_pool", _assess_pool)
    graph.add_node("build_priority_queue", _build_priority_queue)
    graph.add_node("generate_investigation_items", _generate_investigation_items)
    graph.add_node("synthesize_current_advice", _synthesize_current_advice)

    graph.set_entry_point("assess_pool")
    graph.add_conditional_edges(
        "assess_pool",
        _route_after_assess_pool,
        {
            "build_priority_queue": "build_priority_queue",
            "synthesize_current_advice": "synthesize_current_advice",
        },
    )
    graph.add_conditional_edges(
        "build_priority_queue",
        _route_after_priority_queue,
        {
            "generate_investigation_items": "generate_investigation_items",
            "synthesize_current_advice": "synthesize_current_advice",
        },
    )
    graph.add_edge("generate_investigation_items", "synthesize_current_advice")
    graph.add_edge("synthesize_current_advice", END)
    return graph.compile()


investigation_graph = build_investigation_graph()
