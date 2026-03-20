from pydantic import BaseModel, Field
from typing import Optional, Any


# ── Router AI 출력 스키마 (LangChain Structured Output 내부 전용) ─────────────

class RouterResult(BaseModel):
    """Router AI가 반환하는 모드 분류 결과 (내부 전용, API 응답 아님)."""
    selected_mode: int = Field(..., description="선택된 모드 번호 (1~6)", ge=1, le=6)
    reason: str = Field(..., description="모드 선택 이유")


# ── POST /ai-chat 응답 ────────────────────────────────────────────────────────

class PlanItem(BaseModel):
    """계획 항목 하나 (운동 또는 식단 공용)."""
    type: str = Field(
        ...,
        description="운동 종류 또는 식품 종류 (예: '유산소', '닭가슴살 샐러드')",
    )
    detail: str = Field(
        ...,
        description="세부 항목 또는 식사 시간 (예: '러닝 30분', '아침', '월요일')",
    )
    value: str = Field(
        ...,
        description="횟수·세트 또는 수량 (예: '3세트 x 12회', '1인분')",
    )


class Plan(BaseModel):
    """계획 전체 (운동 플랜 또는 식단 플랜)."""
    date: str = Field(
        ...,
        description="날짜 또는 기간 (예: '2026-03-21', '2026-03-21 ~ 2026-03-27')",
    )
    items: list[PlanItem] = Field(..., description="계획 항목 목록")


class DBUpdate(BaseModel):
    """사용자 DB 업데이트 정보 (Mode 6 전용, 프론트 비노출)."""
    field: str = Field(..., description="업데이트할 DB 필드명")
    new_value: Any = Field(..., description="새로운 값")


class ChatData(BaseModel):
    """POST /ai-chat 응답 data 필드."""
    message: str = Field(..., description="사용자에게 보여줄 피드백 메시지")
    plan: Optional[Plan] = Field(None, description="생성/수정된 계획 (Mode 2~5 전용)")
    db_update: Optional[DBUpdate] = Field(
        None,
        description="DB 업데이트 정보 (Mode 6 전용 — 프론트에서 사용자에게 비노출)",
    )


class AIChatResponse(BaseModel):
    """POST /ai-chat 응답 바디."""
    status: str = Field("success", description="처리 상태")
    mode: int = Field(..., description="처리된 모드 번호 (1~6)")
    data: ChatData


# ── POST /process-meal 응답 ───────────────────────────────────────────────────

class MealData(BaseModel):
    """POST /process-meal 응답 data 필드."""
    calories: int = Field(..., description="분석된 총 칼로리 (kcal)")
    message: str = Field(..., description="사용자에게 보여줄 피드백 메시지 (한 줄)")


class MealResponse(BaseModel):
    """POST /process-meal 응답 바디."""
    status: str = Field("success", description="처리 상태")
    data: MealData


# ── POST /recommend 응답 ─────────────────────────────────────────────────────

class RecommendedExercise(BaseModel):
    """추천 운동 정보."""
    name: str = Field(..., description="운동 종류 및 이름")
    burn_calories: int = Field(..., description="예상 소모 칼로리 (kcal)")


class RecommendedMeal(BaseModel):
    """추천 식단 정보."""
    name: str = Field(..., description="식단 종류 및 이름")
    calories: int = Field(..., description="식단 칼로리 (kcal)")


class RecommendData(BaseModel):
    """POST /recommend 응답 data 필드."""
    recommended_exercise: RecommendedExercise
    recommended_meal: RecommendedMeal


class RecommendResponse(BaseModel):
    """POST /recommend 응답 바디."""
    status: str = Field("success", description="처리 상태")
    data: RecommendData


# ── 공통 에러 응답 ────────────────────────────────────────────────────────────

class ErrorResponse(BaseModel):
    """에러 응답 바디."""
    status: str = Field("error", description="처리 상태")
    message: str = Field(..., description="에러 메시지")
    detail: Optional[str] = Field(None, description="상세 에러 정보")
