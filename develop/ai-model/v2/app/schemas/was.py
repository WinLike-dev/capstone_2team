"""WAS request/response schemas and payload normalization helpers."""
from __future__ import annotations

import logging
import re
from datetime import datetime
from typing import Any, Optional

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_DATE_INPUT_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d")
_SETS_PATTERN = re.compile(r"(\d+)")


class WASUserProfile(BaseModel):
    """GET /api/user/profile/{user_id} response."""

    user_id: Optional[str] = None
    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    diet_type: Optional[str] = None
    allergies: Optional[list[str]] = None
    injury_history: Optional[list[str]] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None
    selected_ai_persona: Optional[str] = None

    model_config = {"extra": "allow"}


class WASExerciseItem(BaseModel):
    exercise_name: str
    sets: Optional[int] = None
    duration_minutes: Optional[int] = None
    calories: int = 0


class WASPlanItem(BaseModel):
    """A single workout/meal plan item."""

    id: Optional[str] = None
    name: str
    detail: Optional[str] = None
    day: Optional[str] = None
    ex_list: list[WASExerciseItem] = Field(default_factory=list)
    completed: bool = False

    model_config = {"extra": "allow"}


class WASTodayPlan(BaseModel):
    """GET /api/plan/today/{user_id} response wrapper."""

    items: list[WASPlanItem] = Field(default_factory=list)


class WASProfileUpdateRequest(BaseModel):
    """PUT /api/user/profile/{user_id} request body."""

    weight: Optional[float] = None
    height: Optional[float] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    diet_type: Optional[str] = None
    allergies: Optional[list[str]] = None
    injury_history: Optional[list[str]] = None
    goal: Optional[str] = None
    activity_level: Optional[str] = None

    model_config = {"extra": "forbid"}


class WASPlanCreateRequest(BaseModel):
    """POST /api/plan/create/{user_id} request body."""

    plan_type: str
    items: list[WASPlanItem]

    model_config = {"extra": "forbid"}


class WASPlanUpdateRequest(BaseModel):
    """PUT /api/plan/update/{user_id} request body."""

    plan_type: str
    items: list[WASPlanItem]

    model_config = {"extra": "forbid"}


class WASPlanCheckRequest(BaseModel):
    """PUT /api/plan/check/{user_id} request body."""

    item_id: str

    model_config = {"extra": "forbid"}


def to_profile_update(changes: dict[str, Any]) -> dict[str, Any]:
    """Convert profile_changes into a validated WAS payload."""

    req = WASProfileUpdateRequest.model_validate(changes)
    return req.model_dump(exclude_none=True)


def to_plan_create(extracted: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a proposed new plan into the WAS create payload."""

    if not extracted.get("has_plan") or not extracted.get("items"):
        return None

    plan_type = _normalize_plan_type(extracted.get("plan_type"))
    items = _normalize_plan_items(extracted.get("items"), plan_type)
    if not items:
        logger.warning("Plan create normalization produced no valid items")
        return None

    req = WASPlanCreateRequest(plan_type=plan_type, items=items)
    return req.model_dump(
        exclude_none=True,
        exclude={"items": {"__all__": {"id", "completed"}}},
    )


def to_plan_update(extracted: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a proposed updated plan into the WAS update payload."""

    if not extracted.get("has_changes") or not extracted.get("items"):
        return None

    plan_type = _normalize_plan_type(extracted.get("plan_type"))
    items = _normalize_plan_items(extracted.get("items"), plan_type)
    if not items:
        logger.warning("Plan update normalization produced no valid items")
        return None

    req = WASPlanUpdateRequest(plan_type=plan_type, items=items)
    return req.model_dump(
        exclude_none=True,
        exclude={"items": {"__all__": {"id", "completed"}}},
    )


def to_plan_check(item_id: str) -> dict[str, Any]:
    """Convert item_id into the WAS check payload."""

    req = WASPlanCheckRequest(item_id=item_id)
    return req.model_dump()


def _normalize_plan_type(value: Any) -> str:
    text = str(value or "").strip().lower()
    if text == "diet":
        return "diet"
    return "workout"


def _normalize_plan_items(items: Any, plan_type: str) -> list[dict[str, Any]]:
    if not isinstance(items, list):
        return []

    normalized: list[dict[str, Any]] = []
    for index, item in enumerate(items):
        normalized_item = _normalize_plan_item(item, plan_type)
        if normalized_item:
            normalized.append(normalized_item)
        else:
            logger.warning("Dropped invalid proposed plan item at index=%d", index)
    return normalized


def _normalize_plan_item(item: Any, plan_type: str) -> dict[str, Any] | None:
    if not isinstance(item, dict):
        return None

    name = _first_non_empty(
        item.get("name"),
        item.get("title"),
        item.get("meal_name"),
        item.get("category"),
        default="운동 계획" if plan_type == "workout" else "식단 계획",
    )
    detail = _first_non_empty(
        item.get("detail"),
        item.get("description"),
        item.get("summary"),
        default=None,
    )
    day = _normalize_day(item.get("day") or item.get("date"))

    raw_ex_list = item.get("ex_list")
    if raw_ex_list is None:
        raw_ex_list = item.get("exercise_list")
    if raw_ex_list is None:
        raw_ex_list = item.get("exercises")

    ex_list = [] if plan_type == "diet" else _normalize_exercises(raw_ex_list)

    normalized = WASPlanItem(
        name=name,
        detail=detail,
        day=day,
        ex_list=ex_list,
    )
    return normalized.model_dump(exclude_none=True)


def _normalize_exercises(raw_exercises: Any) -> list[dict[str, Any]]:
    if raw_exercises is None:
        return []

    if isinstance(raw_exercises, dict):
        raw_items = [raw_exercises]
    elif isinstance(raw_exercises, list):
        raw_items = raw_exercises
    elif isinstance(raw_exercises, str):
        raw_items = [{"exercise_name": raw_exercises, "sets": 3, "calories": 0}]
    else:
        return []

    normalized: list[dict[str, Any]] = []
    for raw_item in raw_items:
        if isinstance(raw_item, str):
            exercise_name = raw_item.strip()
            sets = 3
            duration_minutes = None
            calories = 0
        elif isinstance(raw_item, dict):
            exercise_name = _first_non_empty(
                raw_item.get("exercise_name"),
                raw_item.get("name"),
                raw_item.get("exercise"),
                raw_item.get("title"),
                default="",
            )
            sets = _normalize_sets(
                raw_item.get("sets", raw_item.get("set", raw_item.get("count")))
            )
            duration_minutes = _normalize_optional_int(
                raw_item.get("duration_minutes", raw_item.get("duration", raw_item.get("minutes")))
            )
            calories = _normalize_optional_int(raw_item.get("calories")) or 0
        else:
            continue

        if not exercise_name:
            continue

        if duration_minutes is not None:
            sets = None

        normalized.append(
            WASExerciseItem(
                exercise_name=exercise_name,
                sets=sets,
                duration_minutes=duration_minutes,
                calories=calories,
            ).model_dump(exclude_none=True)
        )
    return normalized


def _normalize_day(value: Any) -> Optional[str]:
    if value is None:
        return None

    text = str(value).strip()
    if not text:
        return None

    for fmt in _DATE_INPUT_FORMATS:
        try:
            return datetime.strptime(text, fmt).date().isoformat()
        except ValueError:
            continue
    return text


def _normalize_sets(value: Any) -> int:
    if value is None:
        return 3
    if isinstance(value, bool):
        return 3
    if isinstance(value, int):
        return max(1, value)
    if isinstance(value, float):
        return max(1, int(value))

    match = _SETS_PATTERN.search(str(value))
    if match:
        return max(1, int(match.group(1)))
    return 3


def _normalize_optional_int(value: Any) -> Optional[int]:
    if value is None or value == "":
        return None
    if isinstance(value, bool):
        return None
    if isinstance(value, int):
        return value
    if isinstance(value, float):
        return int(value)

    match = _SETS_PATTERN.search(str(value))
    if match:
        return int(match.group(1))
    return None


def _first_non_empty(*values: Any, default: Optional[str] = None) -> Optional[str]:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text:
            return text
    return default
