"""Modify node for loading the most relevant existing plan context."""
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
    "근력",
    "유산소",
    "하체",
    "상체",
    "전신",
    "러닝",
    "걷기",
    "조깅",
    "스트레칭",
    "세트",
    "횟수",
    "반복",
    "강도",
    "운동량",
    "휴식",
    "쉬는",
    "부담",
    "무릎",
    "허리",
    "어깨",
)
_DIET_KEYWORDS = (
    "식단",
    "식사",
    "메뉴",
    "칼로리",
    "탄수",
    "탄수화물",
    "단백질",
    "지방",
    "간식",
    "아침",
    "점심",
    "저녁",
    "유제품",
    "알레르기",
    "재료",
    "음식",
    "나트륨",
    "당류",
)
_WORKOUT_PRIORITY_KEYWORDS = (
    "강도",
    "운동량",
    "세트",
    "횟수",
    "반복",
    "휴식",
    "쉬는",
    "부담",
    "통증",
    "무릎",
    "허리",
    "어깨",
)
_DIET_PRIORITY_KEYWORDS = (
    "유제품",
    "칼로리",
    "탄수",
    "탄수화물",
    "단백질",
    "지방",
    "메뉴",
    "재료",
    "식사",
    "간식",
    "알레르기",
    "나트륨",
    "당류",
)


def make_modify_node(deps: NodeDeps):
    async def modify_load_node(state: GraphState) -> dict:
        started_at = time.perf_counter()
        user_id = state["user_id"]

        resolved_target, target_source = _infer_modify_target(state)
        deps.trace.record_current_event(
            stage="modify_load",
            status="info",
            title="Modify context load started",
            detail={
                "modify_target": state.get("modify_target"),
                "resolved_target": resolved_target,
                "target_source": target_source,
            },
        )

        try:
            modify_target, plan = await _load_modify_context(
                deps,
                user_id,
                resolved_target,
                target_source,
            )
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
                "target_source": target_source,
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
    target_source: str,
) -> tuple[str | None, dict]:
    if modify_target in {"workout", "diet"}:
        plan = await _load_single_plan(deps, user_id, modify_target)
        if _count_plan_items(plan) > 0:
            return modify_target, plan

        if target_source in {"message", "today_plan"}:
            other_target = "diet" if modify_target == "workout" else "workout"
            other_plan = await _load_single_plan(deps, user_id, other_target)
            if _count_plan_items(other_plan) > 0:
                logger.info(
                    "Primary inferred modify target had no items; switching to populated plan: "
                    "user_id=%s source=%s from=%s to=%s",
                    user_id,
                    target_source,
                    modify_target,
                    other_target,
                )
                return other_target, other_plan
        return modify_target, plan

    logger.info("modify_target missing, probing both plan types: user_id=%s", user_id)
    workout_plan, diet_plan = await _load_both_plans(deps, user_id)
    return _select_populated_plan(workout_plan, diet_plan)


async def _load_single_plan(deps: NodeDeps, user_id: str, plan_type: str) -> dict:
    if plan_type == "workout":
        return await deps.was.get_workout_plan_full(user_id)
    if plan_type == "diet":
        return await deps.was.get_diet_plan_full(user_id)
    return {}


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


def _infer_modify_target(state: GraphState) -> tuple[str | None, str]:
    explicit_target = state.get("modify_target")
    if explicit_target in {"workout", "diet"}:
        return explicit_target, "explicit"

    proposed_plan_type = state.get("proposed_plan_type")
    if proposed_plan_type in {"workout", "diet"}:
        return proposed_plan_type, "proposed_plan"

    message_target = _infer_target_from_message(str(state.get("user_message") or ""))
    if message_target:
        return message_target, "message"

    today_plan_target = _infer_target_from_today_plan(state.get("today_plan") or [])
    if today_plan_target:
        return today_plan_target, "today_plan"

    return None, "unknown"


def _infer_target_from_message(message: str) -> str | None:
    normalized = message.strip().lower()
    if not normalized:
        return None

    if any(keyword in normalized for keyword in _DIET_PRIORITY_KEYWORDS):
        return "diet"
    if any(keyword in normalized for keyword in _WORKOUT_PRIORITY_KEYWORDS):
        return "workout"

    workout_hits = sum(1 for keyword in _WORKOUT_KEYWORDS if keyword in normalized)
    diet_hits = sum(1 for keyword in _DIET_KEYWORDS if keyword in normalized)

    if workout_hits > diet_hits:
        return "workout"
    if diet_hits > workout_hits:
        return "diet"
    return None


def _infer_target_from_today_plan(today_plan: list[dict]) -> str | None:
    if not today_plan:
        return None

    workout_hits = 0
    diet_hits = 0

    for item in today_plan:
        item_type = str(item.get("type") or "").lower()
        item_name = str(item.get("name") or "").lower()
        if item_type == "exercise" or "운동" in item_name:
            workout_hits += 1
        elif item_type == "meal" or any(keyword in item_name for keyword in ("식단", "식사", "아침", "점심", "저녁")):
            diet_hits += 1

    if workout_hits > diet_hits:
        return "workout"
    if diet_hits > workout_hits:
        return "diet"
    if workout_hits:
        return "workout"
    if diet_hits:
        return "diet"
    return None


def _select_populated_plan(workout_plan: dict, diet_plan: dict) -> tuple[str | None, dict]:
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


def _count_plan_items(plan: dict | None) -> int:
    if not isinstance(plan, dict):
        return 0
    items = plan.get("items")
    if not isinstance(items, list):
        return 0
    return len(items)
