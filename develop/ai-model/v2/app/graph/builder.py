"""LangGraph builder for the v2 main flow."""
from __future__ import annotations

from langgraph.checkpoint.base import BaseCheckpointSaver
from langgraph.graph import END, START, StateGraph

from app.graph.deps import NodeDeps
from app.graph.nodes.care import make_care_node
from app.graph.nodes.fallback import make_fallback_node
from app.graph.nodes.generate import make_generate_node
from app.graph.nodes.intent import make_intent_node
from app.graph.nodes.modify import make_modify_node
from app.graph.nodes.persona import make_persona_node
from app.graph.nodes.preprocess import make_preprocess_node
from app.graph.nodes.record import make_record_node
from app.graph.nodes.safety import make_safety_node
from app.graph.nodes.search import make_search_node
from app.schemas.state import GraphState


def route_intent(state: GraphState) -> str:
    intent = state.get("intent", "fallback")
    mapping = {
        "casual": "generate",
        "안전경고": "safety",
        "fallback": "fallback",
        "공감_케어": "care",
        "기록": "record",
        "계획": "search",
        "수정": "modify_load",
        "정보": "search",
        "계획_승인": "generate",
        "home_recommendation": "generate",
    }
    return mapping.get(intent, "fallback")


def route_care(state: GraphState) -> str:
    if state.get("requires_past_memory", False):
        return "search"
    return "generate"


def route_fallback(state: GraphState) -> str:
    if state.get("needs_clarification", False):
        return END
    return "analyze_intent"


def route_search_retry(state: GraphState) -> str:
    quality = state.get("search_quality", "ok")
    results = state.get("search_results") or []
    retry = state.get("search_retry_count", 0)

    if quality == "degraded":
        return "generate"
    if results:
        return "generate"
    if retry > 0:
        return "search"
    return "generate"


def route_generate_self_eval(state: GraphState):
    if state.get("request_kind") == "home_recommendation":
        return END
    if state.get("response"):
        return "persona"
    if state.get("self_eval_failure_reason"):
        return "generate"
    return "persona"


def build_graph(deps: NodeDeps, checkpointer: BaseCheckpointSaver):
    """Build and compile the LangGraph state machine."""
    builder = StateGraph(GraphState)

    builder.add_node("preprocess", make_preprocess_node(deps))
    builder.add_node("analyze_intent", make_intent_node(deps))
    builder.add_node("safety", make_safety_node(deps))
    builder.add_node("care", make_care_node(deps))
    builder.add_node("record", make_record_node(deps))
    builder.add_node("search", make_search_node(deps))
    builder.add_node("modify_load", make_modify_node(deps))
    builder.add_node("fallback", make_fallback_node(deps))
    builder.add_node("generate", make_generate_node(deps))
    builder.add_node("persona", make_persona_node(deps))

    builder.add_edge(START, "preprocess")
    builder.add_edge("preprocess", "analyze_intent")

    builder.add_conditional_edges(
        "analyze_intent",
        route_intent,
        {
            "generate": "generate",
            "safety": "safety",
            "fallback": "fallback",
            "care": "care",
            "record": "record",
            "search": "search",
            "modify_load": "modify_load",
        },
    )

    builder.add_conditional_edges(
        "care",
        route_care,
        {"search": "search", "generate": "generate"},
    )

    builder.add_edge("record", "generate")
    builder.add_edge("modify_load", "search")

    builder.add_conditional_edges(
        "search",
        route_search_retry,
        {"search": "search", "generate": "generate"},
    )

    builder.add_conditional_edges(
        "fallback",
        route_fallback,
        {"analyze_intent": "analyze_intent", END: END},
    )

    builder.add_conditional_edges(
        "generate",
        route_generate_self_eval,
        {"generate": "generate", "persona": "persona", END: END},
    )

    builder.add_edge("persona", END)
    builder.add_edge("safety", END)

    return builder.compile(checkpointer=checkpointer)
