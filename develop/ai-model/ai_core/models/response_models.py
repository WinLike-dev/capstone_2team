from pydantic import BaseModel, Field
from typing import Optional


# ── Router AI 출력 스키마 (LangChain Structured Output 내부 전용) ─────────────

class RouterResult(BaseModel):
    """Router AI가 반환하는 모드 분류 결과 (내부 전용, API 응답 아님)."""
    selected_mode: int = Field(..., description="선택된 모드 번호 (1~6)", ge=1, le=6)
    reason: str = Field(..., description="모드 선택 이유")


# ── POST /ai-chat 응답 ────────────────────────────────────────────────────────

class ChatData(BaseModel):
    """POST /ai-chat 응답 data 필드."""
    message: str = Field(..., description="사용자에게 보여줄 피드백 메시지")


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
