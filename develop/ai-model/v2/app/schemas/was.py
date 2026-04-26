"""WAS request/response schemas and payload normalization helpers."""
from __future__ import annotations

import logging
import re
from datetime import datetime, timedelta
from typing import Any, Optional
from zoneinfo import ZoneInfo

from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_DATE_INPUT_FORMATS = ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d")
_SETS_PATTERN = re.compile(r"(\d+)")
_KST = ZoneInfo("Asia/Seoul")
_MEAL_KEYWORDS = {
    "breakfast",
    "lunch",
    "dinner",
    "snack",
    "brunch",
    "meal",
    "아침",
    "점심",
    "저녁",
    "간식",
    "야식",
    "식단",
    "식사",
}
_WORKOUT_KEYWORDS = {
    "workout",
    "exercise",
    "cardio",
    "strength",
    "stretch",
    "session",
    "routine",
    "운동",
    "유산소",
    "근력",
    "스트레칭",
    "루틴",
}
_WEEKDAY_KEYWORDS = {
    "월요일": 0,
    "화요일": 1,
    "수요일": 2,
    "목요일": 3,
    "금요일": 4,
    "토요일": 5,
    "일요일": 6,
}


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

    payloads = to_plan_create_batches(extracted)
    if not payloads:
        return None

    if len(payloads) > 1:
        logger.warning("Plan create normalization produced multiple payloads; use to_plan_create_batches")
        return None

    return payloads[0]


def to_plan_update(extracted: dict[str, Any]) -> dict[str, Any] | None:
    """Convert a proposed updated plan into the WAS update payload."""

    payloads = to_plan_update_batches(extracted)
    if not payloads:
        return None

    if len(payloads) > 1:
        logger.warning("Plan update normalization produced multiple payloads; use to_plan_update_batches")
        return None

    return payloads[0]


def to_plan_check(item_id: str) -> dict[str, Any]:
    """Convert item_id into the WAS check payload."""

    req = WASPlanCheckRequest(item_id=item_id)
    return req.model_dump()


def to_plan_create_batches(extracted: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a proposed new plan into one or more WAS create payloads."""

    return _build_plan_payload_batches(extracted, update_mode=False)


def to_plan_update_batches(extracted: dict[str, Any]) -> list[dict[str, Any]]:
    """Convert a proposed updated plan into one or more WAS update payloads."""

    return _build_plan_payload_batches(extracted, update_mode=True)


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


def _build_plan_payload_batches(extracted: dict[str, Any], *, update_mode: bool) -> list[dict[str, Any]]:
    required_flag = "has_changes" if update_mode else "has_plan"
    if not extracted.get(required_flag) or not extracted.get("items"):
        return []

    plan_type = _normalize_plan_type(extracted.get("plan_type"))
    grouped_items = _normalize_plan_items_by_type(extracted.get("items"), plan_type)
    if not grouped_items:
        logger.warning(
            "Plan %s normalization produced no valid items",
            "update" if update_mode else "create",
        )
        return []

    request_type = WASPlanUpdateRequest if update_mode else WASPlanCreateRequest
    payloads: list[dict[str, Any]] = []
    for grouped_plan_type, items in grouped_items:
        req = request_type(plan_type=grouped_plan_type, items=items)
        payloads.append(
            req.model_dump(
                exclude_none=True,
                exclude={"items": {"__all__": {"id", "completed"}}},
            )
        )
    return payloads


def _normalize_plan_items_by_type(items: Any, default_plan_type: str) -> list[tuple[str, list[dict[str, Any]]]]:
    if not isinstance(items, list):
        return []

    grouped: dict[str, list[dict[str, Any]]] = {"workout": [], "diet": []}
    ordered_types: list[str] = []

    for index, item in enumerate(items):
        plan_type = _infer_item_plan_type(item, default_plan_type)
        normalized_item = _normalize_plan_item(item, plan_type)
        if not normalized_item:
            logger.warning("Dropped invalid proposed plan item at index=%d", index)
            continue

        if plan_type not in ordered_types:
            ordered_types.append(plan_type)
        grouped[plan_type].append(normalized_item)

    return [
        (plan_type, grouped[plan_type])
        for plan_type in ordered_types
        if grouped[plan_type]
    ]


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
    day = _normalize_day(
        item.get("day") or item.get("date"),
        name=name,
        detail=detail,
    )

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


def _infer_item_plan_type(item: Any, default_plan_type: str) -> str:
    if not isinstance(item, dict):
        return default_plan_type

    name = _first_non_empty(
        item.get("name"),
        item.get("title"),
        item.get("meal_name"),
        item.get("category"),
        default="",
    ) or ""
    detail = _first_non_empty(
        item.get("detail"),
        item.get("description"),
        item.get("summary"),
        default="",
    ) or ""
    combined = f"{name} {detail}".strip().lower()

    if any(keyword in combined for keyword in _MEAL_KEYWORDS):
        return "diet"

    if any(keyword in combined for keyword in _WORKOUT_KEYWORDS):
        return "workout"

    raw_ex_list = item.get("ex_list")
    if raw_ex_list is None:
        raw_ex_list = item.get("exercise_list")
    if raw_ex_list is None:
        raw_ex_list = item.get("exercises")

    if _normalize_exercises(raw_ex_list):
        return "workout"

    return default_plan_type


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


def _normalize_day(
    value: Any,
    *,
    name: str | None = None,
    detail: str | None = None,
) -> Optional[str]:
    if value is None:
        return _infer_day_from_text(name, detail)

    text = str(value).strip()
    if not text:
        return _infer_day_from_text(name, detail)

    for fmt in _DATE_INPUT_FORMATS:
        try:
            parsed = datetime.strptime(text, fmt).date()
            if parsed.year < datetime.now(_KST).year:
                inferred = _infer_day_from_text(name, detail)
                if inferred:
                    return inferred
            return parsed.isoformat()
        except ValueError:
            continue
    return _infer_day_from_text(name, detail) or text


def _infer_day_from_text(name: str | None, detail: str | None) -> Optional[str]:
    combined = " ".join(part for part in (name, detail) if part).strip()
    if not combined:
        return None

    today = datetime.now(_KST).date()
    week_start = today - timedelta(days=today.weekday())
    next_week_start = week_start + timedelta(days=7)
    use_next_week = "다음 주" in combined or "다음주" in combined
    base_week = next_week_start if use_next_week else week_start

    for keyword, weekday_index in _WEEKDAY_KEYWORDS.items():
        if keyword in combined:
            return (base_week + timedelta(days=weekday_index)).isoformat()

    if "오늘" in combined:
        return today.isoformat()
    if "내일" in combined:
        return (today + timedelta(days=1)).isoformat()

    return None


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
