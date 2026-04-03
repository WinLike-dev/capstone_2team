"""채팅 엔드포인트 — POST /chat.

흐름:
1. 초기 GraphState 구성
2. LangGraph graph.ainvoke() 실행
3. 응답 반환
4. BackgroundTasks: WAS 쓰기 + 피드백 루프
"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Request

from app.graph.nodes.feedback import execute_feedback
from app.graph.nodes.was_write import execute_was_writes
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    background_tasks: BackgroundTasks,
    request: Request,
) -> ChatResponse:
    graph = request.app.state.graph
    deps = request.app.state.deps

    session_id = req.session_id or str(uuid.uuid4())
    config = {"configurable": {"thread_id": session_id}}

    # ── 세션 존재 여부 확인 (checkpointer 기반) ──────────────────────────────
    saved = await graph.aget_state(config)
    is_new_session = not saved or not saved.values

    if is_new_session:
        # 첫 턴: 전체 초기 State
        initial_state: GraphState = {
            "user_id": req.user_id,
            "user_message": req.user_message,
            "user_profile": None,
            "today_plan": None,
            "turn_count": 0,
            "is_session_start": True,
            "intent": "",
            "confidence": 0.0,
            "emotion": None,
            "previous_intent": None,
            "previous_emotion": None,
            "requires_past_memory": False,
            "should_save_episode": False,
            "has_fact_change": False,
            "record_type": None,
            "profile_changes": None,
            "is_today": None,
            "modify_target": None,
            "search_targets": [],
            "modify_plan_context": None,
            "search_results": [],
            "search_quality": "ok",
            "search_retry_count": 0,
            "search_query": None,
            "pending_writes": [],
            "response": None,
            "self_eval_count": 0,
            "self_eval_failure_reason": None,
            "fallback_count": 0,
            "needs_clarification": False,
            "summary": None,
            "messages": [],
        }
    else:
        # 이후 턴: 메시지와 응답 초기화만 전달 (나머지는 checkpoint에서 복원)
        initial_state = {
            **saved.values,
            "user_id": req.user_id,
            "user_message": req.user_message,
            "response": None,
            "is_session_start": False,
        }

    # ── 그래프 실행 ───────────────────────────────────────────────────────────
    result: GraphState = await graph.ainvoke(initial_state, config=config)

    response_text = result.get("response") or "죄송해요, 응답을 생성하지 못했어요."
    emotion = result.get("emotion")

    # ── 백그라운드: WAS 쓰기 + 피드백 루프 ───────────────────────────────────
    background_tasks.add_task(
        execute_was_writes,
        deps=deps,
        user_id=req.user_id,
        intent=result.get("intent", ""),
        response=response_text,
        profile_changes=result.get("profile_changes"),
        today_plan=result.get("today_plan"),
        search_results=result.get("search_results"),
        modify_target=result.get("modify_target"),
        modify_plan_context=result.get("modify_plan_context"),
    )

    background_tasks.add_task(
        execute_feedback,
        deps=deps,
        user_id=req.user_id,
        user_message=req.user_message,
        response=response_text,
        should_save_episode=result.get("should_save_episode", False),
        emotion_label=emotion["label"] if emotion else "중립",
        emotion_intensity=emotion["intensity"] if emotion else 0.0,
    )

    return ChatResponse(
        session_id=session_id,
        response=response_text,
        intent=result.get("intent"),
        emotion=emotion,
    )
