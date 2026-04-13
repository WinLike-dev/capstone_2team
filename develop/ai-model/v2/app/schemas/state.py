"""Shared LangGraph state for the v2 model."""
from __future__ import annotations

from typing import Annotated, Any, Literal, Optional

from typing_extensions import TypedDict

from app.core.config import get_settings


def _append_messages(existing: list[dict], new: list[dict] | dict) -> list[dict]:
    if isinstance(new, dict):
        new = [new]
    combined = existing + new
    return combined[-get_settings().MAX_MESSAGES :]


class EmotionState(TypedDict):
    label: str
    intensity: float


class PendingWrite(TypedDict):
    write_type: str
    payload: dict[str, Any]


class DraftComponents(TypedDict):
    core_message: str
    reason_points: list[str]
    suggested_action: str
    safety_notes: list[str]
    approval_question: Optional[str]
    search_grounding_summary: str


RequestKind = Literal["chat", "home_recommendation"]
HomeRecommendationScope = Literal["all", "workout", "diet"]


class GraphState(TypedDict):
    user_id: str
    user_message: str
    request_kind: RequestKind

    user_profile: Optional[dict[str, Any]]
    today_plan: Optional[list[dict[str, Any]]]

    turn_count: int
    is_session_start: bool

    intent: str
    confidence: float
    emotion: Optional[EmotionState]
    previous_intent: Optional[str]
    previous_emotion: Optional[EmotionState]

    requires_past_memory: bool
    should_save_episode: bool
    short_term_memory_query: bool
    has_fact_change: bool
    record_type: Optional[str]
    profile_changes: Optional[dict[str, Any]]
    is_today: Optional[bool]
    modify_target: Optional[str]
    search_targets: list[str]
    modify_plan_context: Optional[dict[str, Any]]

    search_results: list[dict[str, Any]]
    search_quality: str
    search_retry_count: int
    search_query: Optional[str]

    pending_writes: list[PendingWrite]
    awaiting_plan_confirmation: bool

    draft_response: Optional[str]
    draft_components: Optional[DraftComponents]
    proposed_plan: Optional[list[dict[str, Any]]]
    proposed_plan_type: Optional[str]
    proposed_plan_action: Optional[str]
    home_recommendation_scope: Optional[HomeRecommendationScope]
    home_recommendations: Optional[dict[str, Any]]
    intimacy_level: int
    resolved_persona_id: Optional[str]
    profile_sync_version: int

    response: Optional[str]
    self_eval_count: int
    self_eval_failure_reason: Optional[str]

    fallback_count: int
    needs_clarification: bool

    summary: Optional[str]
    last_assistant_message: Optional[str]
    messages: Annotated[list[dict[str, Any]], _append_messages]
