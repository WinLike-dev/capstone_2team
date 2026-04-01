"""
헬스 메이트 - LangGraph StateGraph 조립 및 컴파일

[파이프라인 흐름]

  START
    │
    ▼
  [super_agent]  ── confidence < 0.7 ──────────────────────┐
    │                                                        │
    ├─ intent='운동' & confidence >= 0.7 → [exercise_expert] │
    │                                          │             │
    └─ intent='식단' & confidence >= 0.7 → [diet_expert]    │
                                               │             │
                                    ┌──────────┘             │
                                    ▼                        │
                              [plan_draft]                   │
                                    │                        │
                                    ▼                        │
                              [evaluator]                    │
                                    │                        │
                    ┌── is_safe=True → END                   │
                    │                                        │
                    └── is_safe=False → [reask] ─────────────┘
                                            │
                                           END

[제외된 노드 - 추후 구현 예정]
  검색 라우터 / 탐색 횟수 초과 / Web Search / RAG Search / 문서 평가
"""
from langgraph.graph import StateGraph, START, END

from app.graph.state import HealthMateState
from app.graph.nodes import (
    super_agent_node,
    exercise_expert_node,
    diet_expert_node,
    plan_draft_node,
    evaluator_node,
    reask_node,
)


# ── Conditional Edge 라우팅 함수 ─────────────────────────────────────────────

def route_after_super_agent(state: HealthMateState) -> str:
    """
    Super Agent 이후 라우팅 결정.
    - confidence < 0.7  → 재질문 요청
    - intent == '운동'  → 운동 전문가
    - intent == '식단'  → 식단 전문가
    """
    if (state.get("confidence") or 0.0) < 0.7:
        return "reask"

    intent = state.get("intent", "")
    if intent == "운동":
        return "exercise_expert"
    elif intent == "식단":
        return "diet_expert"
    else:
        # intent가 예상 값이 아닌 경우 안전하게 재질문으로 처리
        return "reask"


def route_after_evaluator(state: HealthMateState) -> str:
    """
    최종 답변 평가 이후 라우팅 결정.
    - is_safe=True  → 최종 플랜 확정 후 종료(END)
    - is_safe=False → 재질문 요청
    """
    if state.get("is_safe") is True:
        return "end"
    return "reask"


# ── Graph 빌드 및 컴파일 ──────────────────────────────────────────────────────

def build_graph() -> StateGraph:
    """
    StateGraph를 조립하고 컴파일된 그래프를 반환한다.
    FastAPI 앱 시작 시 한 번만 호출하여 전역으로 사용한다.
    """
    builder = StateGraph(HealthMateState)

    # ── 노드 등록 ──────────────────────────────────────────
    builder.add_node("super_agent",      super_agent_node)
    builder.add_node("exercise_expert",  exercise_expert_node)
    builder.add_node("diet_expert",      diet_expert_node)
    builder.add_node("plan_draft",       plan_draft_node)
    builder.add_node("evaluator",        evaluator_node)
    builder.add_node("reask",            reask_node)

    # ── 엣지: 진입점 ───────────────────────────────────────
    builder.add_edge(START, "super_agent")

    # ── 조건부 엣지: Super Agent → 전문가 or 재질문 ──────────
    builder.add_conditional_edges(
        "super_agent",
        route_after_super_agent,
        {
            "exercise_expert": "exercise_expert",
            "diet_expert":     "diet_expert",
            "reask":           "reask",
        },
    )

    # ── 일반 엣지: 전문가 → 플랜 초안 (검색 노드 생략) ────────
    builder.add_edge("exercise_expert", "plan_draft")
    builder.add_edge("diet_expert",     "plan_draft")

    # ── 일반 엣지: 플랜 초안 → 평가 ──────────────────────────
    builder.add_edge("plan_draft", "evaluator")

    # ── 조건부 엣지: 평가 → END or 재질문 ─────────────────────
    builder.add_conditional_edges(
        "evaluator",
        route_after_evaluator,
        {
            "end":   END,
            "reask": "reask",
        },
    )

    # ── 일반 엣지: 재질문 → END ────────────────────────────────
    builder.add_edge("reask", END)

    return builder.compile()


# 앱 전역에서 공유할 컴파일된 그래프 인스턴스
graph = build_graph()
