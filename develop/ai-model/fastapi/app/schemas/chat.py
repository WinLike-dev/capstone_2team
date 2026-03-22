"""AI chat request/response schemas.

Implements the DataFormat_3_ai.md specification:
  Request:  POST /ai-chat { user_id, user_profile, user_instruction, user_message }
  Response: { status, mode, data: { message, plan?, db_update? }, db_modified_flag }

db_modified_flag is determined by FastAPI (not Gemini) via get_db_modified_flag().
"""

from typing import Any, Literal, Optional

from pydantic import BaseModel

from app.schemas.common import UserProfile

# ---------------------------------------------------------------------------
# Type aliases
# ---------------------------------------------------------------------------

DbModifiedFlag = Literal["none", "exercise", "meal", "profile"]

# ---------------------------------------------------------------------------
# Request schema
# ---------------------------------------------------------------------------


class AiChatRequest(BaseModel):
    """Incoming /ai-chat request body."""

    user_id: str
    user_profile: UserProfile
    user_instruction: str = ""
    user_message: str


# ---------------------------------------------------------------------------
# Response sub-schemas
# ---------------------------------------------------------------------------


class PlanItem(BaseModel):
    """Single item in a structured daily plan."""

    type: str
    detail: str
    value: str


class PlanData(BaseModel):
    """Structured daily plan (exercise or meal)."""

    date: str
    items: list[PlanItem]


class DbUpdate(BaseModel):
    """Describes a user profile or plan update written to DB."""

    field: str
    new_value: Any


class AiChatData(BaseModel):
    """Payload nested inside AiChatResponse.data."""

    message: str
    plan: Optional[PlanData] = None
    db_update: Optional[DbUpdate] = None
    detail: Optional[Any] = None


# ---------------------------------------------------------------------------
# Response schema
# ---------------------------------------------------------------------------


class AiChatResponse(BaseModel):
    """Outgoing /ai-chat response body."""

    status: str = "success"
    mode: int
    data: AiChatData
    db_modified_flag: DbModifiedFlag


# ---------------------------------------------------------------------------
# Mode-to-flag mapping helper
# ---------------------------------------------------------------------------

_MODE_TO_FLAG: dict[int, DbModifiedFlag] = {
    2: "exercise",
    3: "exercise",
    4: "meal",
    5: "meal",
    6: "profile",
}


def get_db_modified_flag(mode: int) -> DbModifiedFlag:
    """Return the DbModifiedFlag for a given mode.

    Mode-to-flag mapping (per project decision — FastAPI decides, not Gemini):
      mode 2, 3  -> "exercise"
      mode 4, 5  -> "meal"
      mode 6     -> "profile"
      all others -> "none"
    """
    return _MODE_TO_FLAG.get(mode, "none")
