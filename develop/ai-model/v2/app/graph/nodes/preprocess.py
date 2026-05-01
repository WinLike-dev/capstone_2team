"""Preprocess node for session hydration and profile refresh."""
from __future__ import annotations

import logging
import time

from app.core.conversation_state import empty_context_resolution
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
            "action_intent": None,
            "domain": "general",
            "support_mode": "normal",
            "ambiguous": False,
            "context_resolution": empty_context_resolution(),
            "search_results": [],
            "search_quality": "ok",
            "search_retry_count": 0,
            "search_query": None,
            "profile_changes": None,
            "modify_plan_context": None,
            "draft_response": None,
            "draft_components": None,
            "response": None,
            "self_eval_count": 0,
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
            profile_override = state.get("user_profile") if state.get("profile_override_applied") else None
            profile, profile_loaded = await _load_user_profile_with_fallback(
                deps=deps,
                user_id=user_id,
                fallback=state.get("user_profile"),
                context="initial",
            )
            if profile_override:
                profile = _normalize_user_profile({**profile, **profile_override})
            today_plan, today_plan_loaded = await _load_today_plan_with_fallback(
                deps=deps,
                user_id=user_id,
                fallback=state.get("today_plan"),
                context="initial",
            )

            updates["user_profile"] = profile
            updates["today_plan"] = today_plan
            updates["profile_sync_version"] = current_profile_version if profile_loaded else state_profile_version

            deps.trace.record_current_event(
                stage="preprocess",
                status="ok" if profile_loaded or today_plan_loaded else "warn",
                title="Initial WAS hydration completed",
                detail={
                    "profile_loaded": profile_loaded,
                    "today_plan_loaded": today_plan_loaded,
                    "profile_sync_version": updates["profile_sync_version"],
                    "today_plan_items": len(today_plan or []),
                },
            )
            updates["is_session_start"] = False
        elif should_refresh_profile:
            profile, profile_loaded = await _load_user_profile_with_fallback(
                deps=deps,
                user_id=user_id,
                fallback=state.get("user_profile"),
                context="refresh",
            )
            updates["user_profile"] = profile
            updates["profile_sync_version"] = current_profile_version if profile_loaded else state_profile_version
            deps.trace.record_current_event(
                stage="preprocess",
                status="ok" if profile_loaded else "warn",
                title="Profile refresh from WAS completed",
                detail={
                    "profile_loaded": profile_loaded,
                    "profile_sync_version": updates["profile_sync_version"],
                },
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


async def _load_user_profile_with_fallback(
    *,
    deps: NodeDeps,
    user_id: str,
    fallback: dict | None,
    context: str,
) -> tuple[dict, bool]:
    try:
        profile = await deps.was.get_user_profile(user_id)
        logger.info("WAS user_profile load succeeded: user_id=%s context=%s", user_id, context)
        return _normalize_user_profile(profile), True
    except ExternalServiceError as exc:
        if exc.is_http_status(404):
            logger.info("WAS user_profile missing; using empty default: user_id=%s context=%s", user_id, context)
            deps.trace.record_current_alert(
                severity="warning",
                message="WAS user_profile missing; default profile applied",
                detail={"user_id": user_id, "context": context, "status_code": exc.external_status_code},
            )
            return _normalize_user_profile(None), True

        logger.warning("WAS user_profile load failed; using cached fallback: user_id=%s context=%s error=%s", user_id, context, exc)
        deps.trace.record_current_alert(
            severity="warning",
            message="WAS user_profile load failed; cached fallback applied",
            detail={"user_id": user_id, "context": context, "error": str(exc)},
        )
        return _normalize_user_profile(fallback), False


async def _load_today_plan_with_fallback(
    *,
    deps: NodeDeps,
    user_id: str,
    fallback: list[dict] | None,
    context: str,
) -> tuple[list[dict], bool]:
    try:
        today_plan = await deps.was.get_today_plan(user_id)
        logger.info("WAS today_plan load succeeded: user_id=%s context=%s items=%s", user_id, context, len(today_plan or []))
        return _normalize_today_plan(today_plan), True
    except ExternalServiceError as exc:
        if exc.is_http_status(404):
            logger.info("WAS today_plan missing; using empty default: user_id=%s context=%s", user_id, context)
            deps.trace.record_current_alert(
                severity="warning",
                message="WAS today_plan missing; empty plan applied",
                detail={"user_id": user_id, "context": context, "status_code": exc.external_status_code},
            )
            return [], True

        logger.warning("WAS today_plan load failed; using cached fallback: user_id=%s context=%s error=%s", user_id, context, exc)
        deps.trace.record_current_alert(
            severity="warning",
            message="WAS today_plan load failed; cached fallback applied",
            detail={"user_id": user_id, "context": context, "error": str(exc)},
        )
        return _normalize_today_plan(fallback), False


def _normalize_user_profile(profile: dict | None) -> dict:
    normalized = dict(profile or {})
    normalized.setdefault("allergies", [])
    normalized.setdefault("injury_history", [])
    return normalized


def _normalize_today_plan(today_plan: list[dict] | None) -> list[dict]:
    return [dict(item) for item in (today_plan or [])]
