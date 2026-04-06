"""Internal endpoints for WAS push events."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Request

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
) -> ProfileUpdatedEventResponse:
    tracker = request.app.state.profile_sync
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
    return ProfileUpdatedEventResponse(
        user_id=payload.user_id,
        tracked_version=tracked_version,
    )
