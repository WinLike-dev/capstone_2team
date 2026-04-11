"""Preprocess node for session hydration and profile refresh."""
from __future__ import annotations

import logging
import time

from app.core.exceptions import ExternalServiceError
from app.graph.deps import NodeDeps
from app.schemas.state import GraphState

logger = logging.getLogger(__name__)


def make_preprocess_node(deps: NodeDeps):
    async def preprocess_node(state: GraphState) -> dict:
        started_at = time.perf_counter()
        deps.trace.record_current_event(
            stage="preprocess",
            status="info",
            title="Preprocess started",
            detail={
                "is_session_start": bool(state.get("is_session_start", True)),
                "pending_writes": len(state.get("pending_writes", [])),
            },
        )
        updates: dict = {
            "search_results": [],
            "search_quality": "ok",
            "profile_changes": None,
            "modify_plan_context": None,
            "self_eval_failure_reason": None,
            "needs_clarification": False,
        }

        pending = list(state.get("pending_writes", []))
        still_pending = []
        for write in pending:
            try:
                await _execute_write(deps, state["user_id"], write)
                logger.info("Replayed pending write: %s", write["write_type"])
                deps.trace.record_current_event(
                    stage="preprocess",
                    status="ok",
                    title="Pending write replayed",
                    detail={"write_type": write["write_type"]},
                )
            except ExternalServiceError:
                still_pending.append(write)
                logger.warning("Pending write still failing: %s", write["write_type"])
                deps.trace.record_current_alert(
                    severity="warning",
                    message="Pending write replay still failing",
                    detail={"write_type": write["write_type"]},
                )
            except Exception as exc:
                still_pending.append(write)
                logger.warning(
                    "Pending write replay failed with unexpected error: %s (%s)",
                    write["write_type"],
                    exc,
                )
                deps.trace.record_current_alert(
                    severity="error",
                    message="Pending write replay raised unexpected error",
                    detail={"write_type": write["write_type"], "error": str(exc)},
                )
        updates["pending_writes"] = still_pending

        user_id = state["user_id"]
        current_profile_version = await deps.profile_sync.get_profile_version(user_id)
        state_profile_version = int(state.get("profile_sync_version", 0) or 0)
        is_session_start = bool(state.get("is_session_start", True))
        should_refresh_profile = current_profile_version > state_profile_version

        if is_session_start:
            try:
                updates["user_profile"] = await deps.was.get_user_profile(user_id)
                updates["today_plan"] = await deps.was.get_today_plan(user_id)
                updates["profile_sync_version"] = current_profile_version
                logger.info("Initial session load completed: user_id=%s", user_id)
                deps.trace.record_current_event(
                    stage="preprocess",
                    status="ok",
                    title="Initial WAS hydration completed",
                    detail={
                        "profile_sync_version": current_profile_version,
                        "today_plan_items": len(updates["today_plan"] or []),
                    },
                )
            except ExternalServiceError as exc:
                logger.error("Initial WAS load failed: %s", exc)
                updates["user_profile"] = state.get("user_profile")
                updates["today_plan"] = state.get("today_plan")
                updates["profile_sync_version"] = state_profile_version
                deps.trace.record_current_alert(
                    severity="error",
                    message="Initial WAS hydration failed",
                    detail={"error": str(exc)},
                )
            updates["is_session_start"] = False
        elif should_refresh_profile:
            try:
                updates["user_profile"] = await deps.was.get_user_profile(user_id)
                updates["profile_sync_version"] = current_profile_version
                logger.info(
                    "Profile refreshed from WAS after push event: user_id=%s version=%s",
                    user_id,
                    current_profile_version,
                )
                deps.trace.record_current_event(
                    stage="preprocess",
                    status="ok",
                    title="Profile refreshed from WAS",
                    detail={"profile_sync_version": current_profile_version},
                )
            except ExternalServiceError as exc:
                logger.error("Profile refresh after event failed: %s", exc)
                updates["user_profile"] = state.get("user_profile")
                updates["profile_sync_version"] = state_profile_version
                deps.trace.record_current_alert(
                    severity="warning",
                    message="Profile refresh after event failed",
                    detail={"error": str(exc)},
                )

        updates["turn_count"] = state.get("turn_count", 0) + 1
        deps.trace.record_current_event(
            stage="preprocess",
            status="ok",
            title="Preprocess completed",
            detail={"turn_count": updates["turn_count"]},
            duration_ms=round((time.perf_counter() - started_at) * 1000, 2),
        )
        return updates

    return preprocess_node


async def _execute_write(deps: NodeDeps, user_id: str, write: dict) -> None:
    write_type = write["write_type"]
    payload = write["payload"]
    if write_type == "profile":
        await deps.was.put_user_profile(user_id, payload)
    elif write_type == "plan_check":
        await deps.was.put_plan_check(user_id, payload["item_id"])
    elif write_type == "plan_create":
        await deps.was.post_plan_create(user_id, payload)
    elif write_type == "plan_update":
        await deps.was.put_plan_update(user_id, payload)
