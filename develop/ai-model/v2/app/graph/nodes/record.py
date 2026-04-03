"""기록 노드 — Layer 3 기록 의도 상세 구현.

record_type에 따라 처리:
  - profile:    rdb_user_profile 스키마 검증 → State.profile_changes 기록
  - plan_check: is_today 검증 → State.today_plan 완료 체크
"""
from __future__ import annotations

import logging
from typing import Any

from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)

# rdb_user_profile에서 허용하는 필드 목록
_ALLOWED_PROFILE_FIELDS = {
    "weight", "height", "diet_type", "allergies",
    "injury_history", "goal", "activity_level", "age", "gender",
}

_ERR_INVALID_FIELD = "이 항목은 수정할 수 없어요. 수정 가능한 항목: 체중, 키, 식단유형, 알레르기, 부상이력 등"
_ERR_NOT_TODAY = "오늘 플랜만 기록할 수 있어요."
_ERR_NOT_IN_PLAN = "플랜에 없는 항목이에요."


def make_record_node(deps: NodeDeps):
    async def record_node(state: GraphState) -> dict:
        record_type = state.get("record_type")

        if record_type == "profile":
            return await _handle_profile(state)
        elif record_type == "plan_check":
            return await _handle_plan_check(state)
        else:
            logger.warning("record_type이 없음, 기본 응답 처리")
            return {}

    return record_node


async def _handle_profile(state: GraphState) -> dict:
    changes: dict[str, Any] = state.get("profile_changes") or {}

    invalid_fields = set(changes.keys()) - _ALLOWED_PROFILE_FIELDS
    if invalid_fields:
        logger.info("허용되지 않은 필드 변경 시도: %s", invalid_fields)
        return {"response": _ERR_INVALID_FIELD}

    # State 캐시 갱신 (WAS 쓰기는 응답 후 비동기)
    current_profile = dict(state.get("user_profile") or {})
    updated_profile = {**current_profile, **changes}

    return {
        "user_profile": updated_profile,
        "profile_changes": changes,
    }


async def _handle_plan_check(state: GraphState) -> dict:
    if not state.get("is_today", False):
        return {"response": _ERR_NOT_TODAY}

    profile_changes = state.get("profile_changes") or {}
    item_id = profile_changes.get("item_id")

    today_plan: list[dict] = state.get("today_plan") or []
    plan_ids = {item.get("id") for item in today_plan}

    if item_id not in plan_ids:
        return {"response": _ERR_NOT_IN_PLAN}

    # 완료 체크 반영 (WAS 쓰기는 비동기)
    updated_plan = [
        {**item, "completed": True} if item.get("id") == item_id else item
        for item in today_plan
    ]

    return {
        "today_plan": updated_plan,
        "profile_changes": {"item_id": item_id},
    }
