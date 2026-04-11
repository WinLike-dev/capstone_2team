"""Record node for profile updates and today-plan check completion."""
from __future__ import annotations

import logging
from typing import Any

from app.core.exceptions import ExternalServiceError
from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

_ALLOWED_PROFILE_FIELDS = {
    "weight",
    "height",
    "diet_type",
    "allergies",
    "injury_history",
    "goal",
    "activity_level",
    "age",
    "gender",
    "mbti",
}

_ERR_INVALID_FIELD = (
    "지원되지 않는 프로필 항목이에요. 수정 가능한 항목은 체중, 키, 식단유형, "
    "알레르기, 부상 이력, 목표, 활동량, 나이, 성별, MBTI예요."
)
_ERR_NOT_TODAY = "오늘 계획만 기록할 수 있어요."
_ERR_NOT_IN_PLAN = "오늘 계획에 없는 항목이에요."


def make_record_node(deps: NodeDeps):
    async def record_node(state: GraphState) -> dict:
        record_type = state.get("record_type")

        if record_type == "profile":
            return await _handle_profile(state)
        if record_type == "plan_check":
            return await _handle_plan_check(deps, state)

        logger.warning("record_type missing; returning empty update")
        return {}

    return record_node


async def _handle_profile(state: GraphState) -> dict:
    changes: dict[str, Any] = state.get("profile_changes") or {}

    invalid_fields = set(changes.keys()) - _ALLOWED_PROFILE_FIELDS
    if invalid_fields:
        logger.info("Unsupported profile fields detected: %s", sorted(invalid_fields))
        return {"response": _ERR_INVALID_FIELD}

    current_profile = dict(state.get("user_profile") or {})
    updated_profile = {**current_profile, **changes}

    return {
        "user_profile": updated_profile,
        "profile_changes": changes,
    }


async def _handle_plan_check(deps: NodeDeps, state: GraphState) -> dict:
    if not state.get("is_today", False):
        return {"response": _ERR_NOT_TODAY}

    profile_changes = state.get("profile_changes") or {}
    item_id = profile_changes.get("item_id")

    today_plan: list[dict] = state.get("today_plan") or []
    try:
        today_plan = await deps.was.get_today_plan(state["user_id"])
    except ExternalServiceError as exc:
        logger.warning("plan_check refresh failed; using cached today_plan: %s", exc)

    plan_ids = {item.get("id") for item in today_plan}
    if item_id not in plan_ids:
        return {"response": _ERR_NOT_IN_PLAN}

    updated_plan = [
        {**item, "completed": True} if item.get("id") == item_id else item
        for item in today_plan
    ]

    return {
        "today_plan": updated_plan,
        "profile_changes": {"item_id": item_id},
    }
