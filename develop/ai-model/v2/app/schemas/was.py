"""WAS API 요청/응답 스키마 — AI모델 ↔ WAS 간 계약(contract) 레이어.

WAS 팀과 스키마 합의 후 이 파일만 수정하면 전체 연동이 맞춰진다.
내부 State 형식과 WAS 형식 간 변환 함수도 여기서 관리.

TODO: WAS 팀에서 실제 API 스키마 확정 시 아래 모델 필드를 맞출 것.
"""
from __future__ import annotations

from typing import Any, Optional

from pydantic import BaseModel, Field


# ── 읽기 응답 스키마 ─────────────────────────────────────────────────────────

class WASUserProfile(BaseModel):
    """GET /api/user/profile/{user_id} 응답."""
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

    model_config = {"extra": "allow"}  # WAS에서 추가 필드 오면 무시 않고 보존


class WASPlanItem(BaseModel):
    """플랜 항목 하나."""
    id: Optional[str] = None
    name: str
    detail: Optional[str] = None
    day: Optional[str] = None
    completed: bool = False

    model_config = {"extra": "allow"}


class WASTodayPlan(BaseModel):
    """GET /api/plan/today/{user_id} 응답 래퍼."""
    items: list[WASPlanItem] = Field(default_factory=list)


# ── 쓰기 요청 스키마 ─────────────────────────────────────────────────────────

class WASProfileUpdateRequest(BaseModel):
    """PUT /api/user/profile/{user_id} 요청 바디."""
    # 변경할 필드만 포함 (partial update)
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

    model_config = {"extra": "forbid"}


class WASPlanCreateRequest(BaseModel):
    """POST /api/plan/create/{user_id} 요청 바디."""
    plan_type: str  # "workout" | "diet"
    items: list[WASPlanItem]

    model_config = {"extra": "forbid"}


class WASPlanUpdateRequest(BaseModel):
    """PUT /api/plan/update/{user_id} 요청 바디."""
    plan_type: str  # "workout" | "diet"
    items: list[WASPlanItem]

    model_config = {"extra": "forbid"}


class WASPlanCheckRequest(BaseModel):
    """PUT /api/plan/check/{user_id} 요청 바디."""
    item_id: str

    model_config = {"extra": "forbid"}


# ── 변환 함수: 내부 State → WAS 요청 페이로드 ────────────────────────────────

def to_profile_update(changes: dict[str, Any]) -> dict[str, Any]:
    """profile_changes dict → WAS PUT 요청 바디.

    허용되지 않은 필드 자동 제거 + Pydantic 검증.
    """
    req = WASProfileUpdateRequest.model_validate(changes)
    return req.model_dump(exclude_none=True)


def to_plan_create(extracted: dict[str, Any]) -> dict[str, Any] | None:
    """LLM 추출 결과 → WAS POST /plan/create 요청 바디.

    has_plan 등 내부 필드를 제거하고 WAS 형식으로 변환.
    """
    if not extracted.get("has_plan") or not extracted.get("items"):
        return None
    items = [
        WASPlanItem(
            name=item.get("name", ""),
            detail=item.get("detail"),
            day=item.get("day"),
        ).model_dump(exclude_none=True)
        for item in extracted["items"]
    ]
    req = WASPlanCreateRequest(
        plan_type=extracted.get("plan_type", "workout"),
        items=items,
    )
    return req.model_dump()


def to_plan_update(extracted: dict[str, Any]) -> dict[str, Any] | None:
    """LLM 수정 추출 결과 → WAS PUT /plan/update 요청 바디.

    has_changes 등 내부 필드를 제거.
    """
    if not extracted.get("has_changes") or not extracted.get("items"):
        return None
    items = [
        WASPlanItem(
            name=item.get("name", ""),
            detail=item.get("detail"),
            day=item.get("day"),
        ).model_dump(exclude_none=True)
        for item in extracted["items"]
    ]
    req = WASPlanUpdateRequest(
        plan_type=extracted.get("plan_type", "workout"),
        items=items,
    )
    return req.model_dump()


def to_plan_check(item_id: str) -> dict[str, Any]:
    """item_id → WAS PUT /plan/check 요청 바디."""
    req = WASPlanCheckRequest(item_id=item_id)
    return req.model_dump()
