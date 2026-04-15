"""FastAPI endpoint for home-tab recommendations."""
from __future__ import annotations

import time
import uuid

from fastapi import APIRouter, Depends, Request

from app.core.conversation_state import empty_context_resolution, empty_recent_dialogue
from app.core.internal_auth import require_internal_api_key
from app.core.trace_store import bind_trace, reset_trace, timed_ms
from app.schemas.home import HomeRecommendationRequest, HomeRecommendationResponse
from app.schemas.state import GraphState
from app.services.home_recommendations import empty_home_recommendations, kst_today_iso

router = APIRouter(prefix="/home", tags=["home"])


def _build_home_initial_state(req: HomeRecommendationRequest) -> GraphState:
    return {
        "user_id": req.user_id,
        "user_message": f"HOME_RECOMMENDATION:{req.type}",
        "request_kind": "home_recommendation",
        "user_profile": None,
        "today_plan": None,
        "turn_count": 0,
        "is_session_start": True,
        "intent": "",
        "action_intent": None,
        "domain": "general",
        "support_mode": "normal",
        "ambiguous": False,
        "context_resolution": empty_context_resolution(),
        "confidence": 0.0,
        "emotion": None,
        "previous_intent": None,
        "previous_emotion": None,
        "requires_past_memory": False,
        "should_save_episode": False,
        "short_term_memory_query": False,
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
        "awaiting_plan_confirmation": False,
        "active_proposal": None,
        "recent_dialogue": empty_recent_dialogue(),
        "draft_response": None,
        "draft_components": None,
        "proposed_plan": None,
        "proposed_plan_type": None,
        "proposed_plan_action": None,
        "home_recommendation_scope": req.type,
        "home_recommendations": None,
        "home_recommendation_recent": req.recent_recommendations.model_dump() if req.recent_recommendations else None,
        "intimacy_level": 1,
        "resolved_persona_id": None,
        "profile_sync_version": 0,
        "response": None,
        "self_eval_count": 0,
        "self_eval_failure_reason": None,
        "fallback_count": 0,
        "needs_clarification": False,
    }


async def _run_home_recommendations(
    req: HomeRecommendationRequest,
    request: Request,
) -> HomeRecommendationResponse:
    graph = request.app.state.graph
    trace_store = request.app.state.trace_store

    date = kst_today_iso()
    session_id = f"home:{req.user_id}:{date}:{req.type}:{uuid.uuid4().hex[:8]}"
    trace_id = trace_store.start_trace(
        kind="home_recommendation",
        user_id=req.user_id,
        session_id=session_id,
        message=f"HOME_RECOMMENDATION:{req.type}",
        request_payload=req.model_dump(),
        metadata={"entrypoint": "home_recommendations", "scope": req.type},
    )
    token = bind_trace(trace_id)
    request_started_at = time.perf_counter()
    config = {"configurable": {"thread_id": session_id}}

    try:
        trace_store.record_event(
            trace_id,
            stage="request",
            status="info",
            title="Home recommendation request received",
            detail={"scope": req.type},
        )
        result: GraphState = await graph.ainvoke(
            _build_home_initial_state(req),
            config=config,
        )
        payload = result.get("home_recommendations") or empty_home_recommendations(
            date=date,
            scope=req.type,
            user_profile=result.get("user_profile") or {},
            today_plan=result.get("today_plan") or [],
            recent_recommendations=req.recent_recommendations.model_dump()
            if req.recent_recommendations
            else {},
        ).model_dump()
        response = HomeRecommendationResponse.model_validate(payload)

        trace_store.record_event(
            trace_id,
            stage="response",
            status="ok",
            title="Home recommendations returned",
            detail={
                "scope": req.type,
                "workout_slots": sum(
                    1 for item in response.workout.model_dump().values() if item is not None
                ),
                "diet_slots": sum(
                    1 for item in response.diet.model_dump().values() if item is not None
                ),
            },
            duration_ms=timed_ms(request_started_at),
        )
        trace_store.finish_trace(
            trace_id,
            status="response_sent",
            response=response.model_dump(),
            state_summary={
                "intent": result.get("intent"),
                "request_kind": result.get("request_kind"),
                "scope": req.type,
            },
        )
        return response
    finally:
        reset_trace(token)


@router.post(
    "/recommendations",
    response_model=HomeRecommendationResponse,
    dependencies=[Depends(require_internal_api_key)],
)
async def recommend_home_items(
    req: HomeRecommendationRequest,
    request: Request,
) -> HomeRecommendationResponse:
    return await _run_home_recommendations(req, request)


@router.post(
    "/recommendations/workout",
    response_model=HomeRecommendationResponse,
    dependencies=[Depends(require_internal_api_key)],
)
async def recommend_workout_items(
    req: HomeRecommendationRequest,
    request: Request,
) -> HomeRecommendationResponse:
    scoped_req = HomeRecommendationRequest(
        user_id=req.user_id,
        type="workout",
        recent_recommendations=req.recent_recommendations,
    )
    return await _run_home_recommendations(scoped_req, request)


@router.post(
    "/recommendations/diet",
    response_model=HomeRecommendationResponse,
    dependencies=[Depends(require_internal_api_key)],
)
async def recommend_diet_items(
    req: HomeRecommendationRequest,
    request: Request,
) -> HomeRecommendationResponse:
    scoped_req = HomeRecommendationRequest(
        user_id=req.user_id,
        type="diet",
        recent_recommendations=req.recent_recommendations,
    )
    return await _run_home_recommendations(scoped_req, request)
