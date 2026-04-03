"""수정 의도 — 플랜 조회 노드 (Layer 3 수정 의도 상세).

modify_target에 따라 WAS에서 전체 플랜을 동기 호출한다.
조회 결과는 modify_plan_context에 임시 저장 (State에 영구 저장하지 않음).
이후 검색 파이프라인으로 전달된다.
"""
from __future__ import annotations

import logging

from app.core.exceptions import ExternalServiceError
from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)


def make_modify_node(deps: NodeDeps):
    async def modify_load_node(state: GraphState) -> dict:
        modify_target = state.get("modify_target")
        user_id = state["user_id"]

        try:
            if modify_target == "workout":
                plan = await deps.was.get_workout_plan_full(user_id)
            elif modify_target == "diet":
                plan = await deps.was.get_diet_plan_full(user_id)
            else:
                logger.warning("modify_target이 없음: user_id=%s", user_id)
                plan = {}
        except ExternalServiceError as e:
            logger.error("플랜 조회 실패: %s", e)
            plan = {}

        return {"modify_plan_context": plan}

    return modify_load_node
