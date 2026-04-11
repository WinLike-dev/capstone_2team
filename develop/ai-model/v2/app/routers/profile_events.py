"""Internal endpoints for WAS push events."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, Request

from app.core.trace_store import bind_trace, reset_trace
from app.core.internal_auth import require_internal_api_key
from app.schemas.profile_events import (
    ProfileUpdatedEventRequest,
    ProfileUpdatedEventResponse,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/internal/events", tags=["internal"])


@router.post("/profile-updated", response_model=ProfileUpdatedEventResponse)
async def profile_updated(
    payload: ProfileUpdatedEventRequest,
    request: Request,
    _: None = Depends(require_internal_api_key),
) -> ProfileUpdatedEventResponse:
    tracker = request.app.state.profile_sync
    trace_store = request.app.state.trace_store
    trace_id = trace_store.start_trace(
        kind="profile_event",
        user_id=payload.user_id,
        message="profile-updated",
        request_payload=payload.model_dump(),
    )
    token = bind_trace(trace_id)
    try:
        tracked_version = await tracker.mark_profile_updated(
            user_id=payload.user_id,
            profile_version=payload.profile_version,
        )
        logger.info(
            "Profile update event received: user_id=%s tracked_version=%s changed_fields=%s",
            payload.user_id,
            tracked_version,
            payload.changed_fields,
        )
        trace_store.record_event(
            trace_id,
            stage="profile_event",
            status="ok",
            title="Profile update event processed",
            detail={
                "tracked_version": tracked_version,
                "changed_fields": payload.changed_fields,
            },
        )
        trace_store.finish_trace(
            trace_id,
            status="completed",
            response={
                "user_id": payload.user_id,
                "tracked_version": tracked_version,
            },
            state_summary={"changed_fields": payload.changed_fields},
        )
        return ProfileUpdatedEventResponse(
            user_id=payload.user_id,
            tracked_version=tracked_version,
        )
    finally:
        reset_trace(token)
