"""Schemas for internal profile update events sent by WAS."""
from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ProfileUpdatedEventRequest(BaseModel):
    user_id: str = Field(description="User whose WAS profile has changed")
    changed_fields: list[str] = Field(
        default_factory=list,
        description="Fields changed by the WAS profile update",
    )
    profile_version: Optional[int] = Field(
        default=None,
        description="Optional monotonic version from WAS",
    )


class ProfileUpdatedEventResponse(BaseModel):
    status: str = "success"
    user_id: str
    tracked_version: int
