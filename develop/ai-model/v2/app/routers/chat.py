"""FastAPI /chat endpoint."""
from __future__ import annotations

import asyncio
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Request

from app.core.config import get_settings
from app.core.lifespan import update_session_activity
from app.graph.nodes.feedback import execute_feedback
from app.graph.nodes.was_write import execute_was_writes
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

REQUEST_TIMEOUT = 120
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

    saved = await graph.aget_state(config)
    is_new_session = not saved or not saved.values

    if is_new_session:
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
            "draft_response": None,
            "draft_components": None,
            "proposed_plan": None,
            "proposed_plan_type": None,
            "proposed_plan_action": None,
            "intimacy_level": 1,
            "resolved_persona_id": None,
            "profile_sync_version": 0,
            "response": None,
            "self_eval_count": 0,
            "self_eval_failure_reason": None,
            "fallback_count": 0,
            "needs_clarification": False,
            "summary": None,
            "messages": [],
        }
        if req.user_profile_override:
            initial_state["user_profile"] = req.user_profile_override
    else:
        saved_values = {key: value for key, value in saved.values.items() if key != "ai_persona"}
        initial_state = {
            **saved_values,
            "user_id": req.user_id,
            "user_message": req.user_message,
            "response": None,
            "is_session_start": False,
            "modify_plan_context": None,
            "search_results": [],
            "search_query": None,
            "self_eval_failure_reason": None,
            "draft_response": None,
            "draft_components": None,
            "resolved_persona_id": None,
        }
        if req.user_profile_override:
            initial_state["user_profile"] = req.user_profile_override

    try:
        result: GraphState = await asyncio.wait_for(
            graph.ainvoke(initial_state, config=config),
            timeout=REQUEST_TIMEOUT,
        )
    except asyncio.TimeoutError:
        logger.error("Graph request timed out after %ds: session=%s", REQUEST_TIMEOUT, session_id)
        return ChatResponse(
            session_id=session_id,
            response="죄송해요, 처리 시간이 초과됐어요. 다시 시도해 주세요.",
        )

    response_text = result.get("response") or "죄송해요, 응답을 생성하지 못했어요."
    emotion = result.get("emotion")

    settings = get_settings()
    show_debug_state = settings.APP_ENV == "development" or bool(req.user_profile_override)
    background_tasks.add_task(
        update_session_activity,
        settings.CHECKPOINT_DB_PATH,
        session_id,
    )

    background_tasks.add_task(
        _was_write_and_save_pending,
        graph=graph,
        config=config,
        deps=deps,
        user_id=req.user_id,
        intent=result.get("intent", ""),
        response=response_text,
        record_type=result.get("record_type"),
        profile_changes=result.get("profile_changes"),
        today_plan=result.get("today_plan"),
        search_results=result.get("search_results"),
        modify_target=result.get("modify_target"),
        modify_plan_context=result.get("modify_plan_context"),
        proposed_plan=result.get("proposed_plan"),
        proposed_plan_type=result.get("proposed_plan_type"),
        proposed_plan_action=result.get("proposed_plan_action"),
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
        draft_response=result.get("draft_response"),
        debug_state={
            "search_results_count": len(result.get("search_results", [])),
            "search_quality": result.get("search_quality"),
            "draft_components": result.get("draft_components"),
            "proposed_plan_count": len(result.get("proposed_plan") or []),
            "proposed_plan": result.get("proposed_plan"),
            "proposed_plan_type": result.get("proposed_plan_type"),
            "proposed_plan_action": result.get("proposed_plan_action"),
            "selected_ai_persona": (result.get("user_profile") or {}).get("selected_ai_persona"),
            "resolved_persona_id": result.get("resolved_persona_id"),
            "profile_sync_version": result.get("profile_sync_version"),
            "intimacy_level": result.get("intimacy_level"),
            "user_profile_mbti": (result.get("user_profile") or {}).get("mbti"),
        } if show_debug_state else None,
    )


async def _was_write_and_save_pending(
    graph,
    config: dict,
    deps,
    user_id: str,
    intent: str,
    response: str,
    record_type,
    profile_changes,
    today_plan,
    search_results,
    modify_target,
    modify_plan_context,
    proposed_plan,
    proposed_plan_type,
    proposed_plan_action,
) -> None:
    pending = await execute_was_writes(
        deps=deps,
        user_id=user_id,
        intent=intent,
        response=response,
        record_type=record_type,
        profile_changes=profile_changes,
        today_plan=today_plan,
        search_results=search_results,
        modify_target=modify_target,
        modify_plan_context=modify_plan_context,
        proposed_plan=proposed_plan,
        proposed_plan_type=proposed_plan_type,
        proposed_plan_action=proposed_plan_action,
    )
    updates = {}
    if pending:
        updates["pending_writes"] = pending
    elif intent == "계획_승인" and proposed_plan:
        updates = {
            "pending_writes": [],
            "proposed_plan": None,
            "proposed_plan_type": None,
            "proposed_plan_action": None,
        }
    if updates:
        try:
            await graph.aupdate_state(config, updates)
            if pending:
                logger.warning("Saved %d pending writes to checkpoint", len(pending))
        except Exception as exc:
            logger.error("Failed to update pending writes: %s", exc)
