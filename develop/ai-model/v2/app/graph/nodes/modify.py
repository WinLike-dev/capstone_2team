"""Modify node for loading the full workout or diet plan from WAS."""
from __future__ import annotations

import logging
import time

from app.core.exceptions import ExternalServiceError
from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

_WORKOUT_KEYWORDS = (
    "운동",
    "루틴",
    "홈트",
    "근력",
    "유산소",
    "하체",
    "상체",
    "전신",
    "스트레칭",
    "러닝",
)
_DIET_KEYWORDS = (
    "식단",
    "식사",
    "메뉴",
    "아침",
    "점심",
    "저녁",
    "간식",
    "칼로리",
    "유제품",
    "단백질",
)


def make_modify_node(deps: NodeDeps):
    async def modify_load_node(state: GraphState) -> dict:
        started_at = time.perf_counter()
        user_id = state["user_id"]

        resolved_target = _infer_modify_target(state)
        deps.trace.record_current_event(
            stage="modify_load",
            status="info",
            title="Modify context load started",
            detail={
                "modify_target": state.get("modify_target"),
                "resolved_target": resolved_target,
            },
        )

        try:
            modify_target, plan = await _load_modify_context(deps, user_id, resolved_target)
        except ExternalServiceError as exc:
            logger.error("Full plan load failed: %s", exc)
            modify_target = resolved_target
            plan = {}
            deps.trace.record_current_alert(
                severity="error",
                message="Full plan load from WAS failed",
                detail={"modify_target": resolved_target, "error": str(exc)},
            )

        if not modify_target:
            deps.trace.record_current_alert(
                severity="warning",
                message="Modify target missing during full-plan load",
                detail={"user_id": user_id},
            )

        deps.trace.record_current_event(
            stage="modify_load",
            status="ok" if plan else "warn",
            title="Modify context load completed",
            detail={
                "modify_target": modify_target,
                "loaded": bool(plan),
                "item_count": _count_plan_items(plan),
                "top_level_keys": list(plan.keys())[:12] if isinstance(plan, dict) else None,
            },
            duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        return {
            "modify_target": modify_target,
            "modify_plan_context": plan,
        }

    return modify_load_node


async def _load_modify_context(
    deps: NodeDeps,
    user_id: str,
    modify_target: str | None,
) -> tuple[str | None, dict]:
    if modify_target == "workout":
        return "workout", await deps.was.get_workout_plan_full(user_id)

    if modify_target == "diet":
        return "diet", await deps.was.get_diet_plan_full(user_id)

    logger.info("modify_target missing, probing both plan types: user_id=%s", user_id)
    workout_plan, diet_plan = await _load_both_plans(deps, user_id)
    workout_count = _count_plan_items(workout_plan)
    diet_count = _count_plan_items(diet_plan)

    if workout_count > diet_count:
        return "workout", workout_plan
    if diet_count > workout_count:
        return "diet", diet_plan
    if workout_count:
        return "workout", workout_plan
    if diet_count:
        return "diet", diet_plan
    return None, {}


async def _load_both_plans(deps: NodeDeps, user_id: str) -> tuple[dict, dict]:
    workout_plan: dict = {}
    diet_plan: dict = {}

    try:
        workout_plan = await deps.was.get_workout_plan_full(user_id)
    except ExternalServiceError as exc:
        logger.warning("Workout full plan probe failed: %s", exc)

    try:
        diet_plan = await deps.was.get_diet_plan_full(user_id)
    except ExternalServiceError as exc:
        logger.warning("Diet full plan probe failed: %s", exc)

    return workout_plan, diet_plan


def _infer_modify_target(state: GraphState) -> str | None:
    explicit_target = state.get("modify_target")
    if explicit_target in {"workout", "diet"}:
        return explicit_target

    proposed_plan_type = state.get("proposed_plan_type")
    if proposed_plan_type in {"workout", "diet"}:
        return proposed_plan_type

    message = str(state.get("user_message") or "").lower()
    workout_hits = sum(1 for keyword in _WORKOUT_KEYWORDS if keyword in message)
    diet_hits = sum(1 for keyword in _DIET_KEYWORDS if keyword in message)

    if workout_hits > diet_hits:
        return "workout"
    if diet_hits > workout_hits:
        return "diet"

    today_plan = state.get("today_plan") or []
    if today_plan:
        return "workout"

    return None


def _count_plan_items(plan: dict | None) -> int:
    if not isinstance(plan, dict):
        return 0
    items = plan.get("items")
    if not isinstance(items, list):
        return 0
    return len(items)
