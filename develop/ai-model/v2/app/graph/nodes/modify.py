"""Modify node for loading the full workout or diet plan from WAS."""
from __future__ import annotations

import logging
import time

from app.core.exceptions import ExternalServiceError
from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)


def make_modify_node(deps: NodeDeps):
    async def modify_load_node(state: GraphState) -> dict:
        started_at = time.perf_counter()
        modify_target = state.get("modify_target")
        user_id = state["user_id"]
        deps.trace.record_current_event(
            stage="modify_load",
            status="info",
            title="Modify context load started",
            detail={"modify_target": modify_target},
        )

        try:
            if modify_target == "workout":
                plan = await deps.was.get_workout_plan_full(user_id)
            elif modify_target == "diet":
                plan = await deps.was.get_diet_plan_full(user_id)
            else:
                logger.warning("modify_target missing: user_id=%s", user_id)
                plan = {}
                deps.trace.record_current_alert(
                    severity="warning",
                    message="Modify target missing during full-plan load",
                    detail={"user_id": user_id},
                )
        except ExternalServiceError as exc:
            logger.error("Full plan load failed: %s", exc)
            plan = {}
            deps.trace.record_current_alert(
                severity="error",
                message="Full plan load from WAS failed",
                detail={"modify_target": modify_target, "error": str(exc)},
            )

        deps.trace.record_current_event(
            stage="modify_load",
            status="ok" if plan else "warn",
            title="Modify context load completed",
            detail={
                "modify_target": modify_target,
                "loaded": bool(plan),
                "top_level_keys": list(plan.keys())[:12] if isinstance(plan, dict) else None,
            },
            duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        return {"modify_plan_context": plan}

    return modify_load_node
